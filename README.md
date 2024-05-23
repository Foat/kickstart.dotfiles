# kickstart.dotfiles (kdf)

## Overview

This project provides a Python script to manage your `.dotfiles` efficiently. It includes features to clone separate Git repositories, link static files and folders, handle templates with environment variables, and check for differences between generated and template files. The script supports dry-run functionality and backs up existing files before creating new ones.

## Features

- Clone specified Git repositories to desired directories.
- Create symlinks for static files and folders.
- Generate and link files from templates, supporting environment variable substitution.
- Check for differences between generated files and templates (uses `diff` CLI, which should be installed on most systems already).
- Backup existing files before overwriting.
- Support for dry-run mode to preview actions without making changes.

## Configuration

The script uses a JSON configuration file to specify the dotfiles setup. Here is an example `config.json`:

```json
{
  "dotfiles": {
    "content": "./example/content/",
    "generated": "./example/generated@linux/"
  },
  "clone": {
    ".ssh": {
      "url": "https://github.com/nvim-lua/kickstart.nvim",
      "path": "./example/home@linux/.config/nvim"
    }
  },
  "links": {
    ".config/yazi": "./example/home@linux/.config/yazi",
    ".zshrc_add@linux": "./example/home@linux/.zshrc_add"
  },
  "templates": {
    ".zshrc.temp": "./example/home@linux/.zshrc",
    ".config/rclone/rclone.conf.temp": "./example/home@linux/.config/rclone/rclone.conf"
  },
  "env": [
    "TEMP_EXAMPLE_ENV"
  ],
  "env_base64": [
    "TEMP_RCLONE_HOME"
  ]
}
```

## Usage

### First steps

- Fork or clone this repo to have your own copy that you can modify.
- Put your configuration and .dotfiles there.

### Running the Script

To use the dotfiles manager, run the script with the desired options:

```bash
python kdf.py --config path/to/config.json [--dry-run] [--check-templates]
```

### Options

- `--config`: Path to the configuration JSON file (required).
- `--dry-run`: Perform a dry run, showing what actions would be taken without making any changes.
- `--check-templates`: Check if the generated templates differ from the existing files without regenerating templates.

### Example

Perform a dry run with the specified configuration:

```bash
python kdf.py --config config.json --dry-run
```

Check for differences between generated and template files:

```bash
python kdf.py --config config.json --check-templates
```

Run the provided `example`, it will generate files in the `example` folder:

```bash
git clone https://github.com/Foat/kickstart.dotfiles.git
cd .dotfiles
./example/run.sh --config ./example/config@linux.json
```

See `./example/run.sh` for some comments on how to use environment variables.

### Template Variables
In template files, replaceable variables are presented like `{{ TEMP_BW_SESSION }}`. The program will replace these variables with the corresponding environment variable values. You can provide variables in base64 format (used for multiline variables); use the `env_base64` config parameter for that. It will be decoded before replacing the template variable.

## Requirements

- Python 3.8+
- No external dependencies are required.

## Naming

Inspired by https://github.com/nvim-lua/kickstart.nvim project.
