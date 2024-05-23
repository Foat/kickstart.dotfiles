import base64
import json
import os
import shlex
import subprocess
from datetime import datetime
from typing import Any, Dict, List


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r") as file:
        return json.load(file)


def create_folder(dst: str, parent: bool = True, dry_run: bool = True):
    if parent:
        dst_dir = os.path.dirname(dst)
    else:
        dst_dir = dst
    if not os.path.exists(dst_dir):
        if dry_run:
            print(f"Dry-run: create directory {dst_dir}")
        else:
            os.makedirs(dst_dir)


def convert_envs(env: List[str], env_base64: List[str]) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}

    def getenv(name: str) -> str:
        assert (
            name not in env_vars.keys()
        ), f"Env var {name} is already in {env_vars.keys()}, please fix the config"
        env_value = os.getenv(name)
        assert env_value is not None, f"Missing env var {name}"
        return env_value

    for var in env:
        env_vars[var] = getenv(var)

    for var in env_base64:
        value = getenv(var)
        decoded_value = base64.b64decode(value).decode("utf-8")
        env_vars[var] = decoded_value

    return env_vars


def clone_repos(clone_config: Dict[str, Dict[str, str]], dry_run: bool):
    for _, repo in clone_config.items():
        path = os.path.expanduser(repo["path"])
        if dry_run:
            print(f"Dry-run: clone {repo['url']} to {path}")
        else:
            if not os.path.exists(path):
                subprocess.run(["git", "clone", repo["url"], path], check=True)
            else:
                print(f"Path {path} already exists, pulling latest changes.")
                subprocess.run(["git", "-C", path, "pull"], check=True)


def create_symlink(src: str, dst: str, dry_run: bool):
    dst = os.path.expanduser(dst)
    create_folder(dst, dry_run=dry_run)

    if os.path.exists(dst) and not os.path.islink(dst):
        backup_name = f"{dst}.{datetime.now().strftime('%Y%m%d%H%M%S')}.back"
        if dry_run:
            print(f"Dry-run: rename {dst} to {backup_name}")
        else:
            os.rename(dst, backup_name)

    if dry_run:
        print(f"Dry-run: link {src} to {dst}")
    else:
        if os.path.islink(dst):
            os.remove(dst)
        os.symlink(src, dst)


def link_static_files(content_path: str, links_config: Dict[str, str], dry_run: bool):
    for src, dst in links_config.items():
        create_symlink(os.path.join(content_path, src), dst, dry_run)


def generate_templates(
    content_path: str,
    template_config: Dict[str, str],
    env_vars: Dict[str, str],
    generated_path: str,
    dry_run: bool,
):
    for src, dst in template_config.items():
        src_path = os.path.join(content_path, src)
        dst_path = os.path.expanduser(dst)
        with open(src_path, "r") as file:
            content = file.read()

        for var, value in env_vars.items():
            content = content.replace(f"{{{{ {var} }}}}", value)

        generated_file_path = os.path.join(generated_path, src)

        if dry_run:
            print(f"Dry-run: generate {generated_file_path} from {src_path}")
        else:
            create_folder(generated_file_path, dry_run=dry_run)
            with open(generated_file_path, "w") as file:
                file.write(content)
        create_symlink(generated_file_path, dst_path, dry_run)


def check_templates(
    content_path: str,
    template_config: Dict[str, str],
    env_vars: Dict[str, str],
    generated_path: str,
):
    for src, _ in template_config.items():
        src_path = os.path.join(content_path, src)
        with open(src_path, "r") as file:
            content = file.read()

        for var, value in env_vars.items():
            content = content.replace(f"{{{{ {var} }}}}", value)

        generated_file_path = os.path.join(generated_path, src)

        if os.path.exists(generated_file_path):
            content_escaped = shlex.quote(content)
            diff_command = f"diff -y --suppress-common-lines <(echo -n {content_escaped}) {generated_file_path}"
            result = subprocess.run(
                ["bash", "-c", diff_command], capture_output=True, text=True
            )
            if result.stdout:
                print(f"Differences found for {generated_file_path}:")
                print(result.stdout)
            else:
                print(f"No differences found for {generated_file_path}")
        else:
            print(f"Generated file {generated_file_path} does not exist.")


def main(config_path: str, dry_run: bool = False, check: bool = False):
    config = load_config(config_path)
    content_path = os.path.abspath(os.path.expanduser(config["dotfiles"]["content"]))
    generated_path = os.path.abspath(
        os.path.expanduser(config["dotfiles"]["generated"])
    )
    create_folder(generated_path, parent=False, dry_run=dry_run)

    env_vars = convert_envs(config["env"], config["env_base64"])

    if check:
        check_templates(content_path, config["templates"], env_vars, generated_path)
    else:
        clone_repos(config["clone"], dry_run)
        link_static_files(content_path, config["links"], dry_run)
        generate_templates(
            content_path, config["templates"], env_vars, generated_path, dry_run
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage .dotfiles")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the config file"
    )
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    parser.add_argument(
        "--check-templates",
        action="store_true",
        help="Check if generated templates differ from existing files",
    )

    args = parser.parse_args()
    main(args.config, args.dry_run, args.check_templates)
