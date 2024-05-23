import base64
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from kdf import check_templates, convert_envs, generate_templates, link_static_files


class TestDotfilesManager(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "PLAIN_VAR": "plain_value",
            "BASE64_VAR": base64.b64encode(b"base64_value").decode("utf-8"),
        },
    )
    def test_convert_envs(self):
        env = ["PLAIN_VAR"]
        env_base64 = ["BASE64_VAR"]
        result = convert_envs(env, env_base64)

        expected = {"PLAIN_VAR": "plain_value", "BASE64_VAR": "base64_value"}

        self.assertEqual(result, expected)

    @patch.dict(
        os.environ,
        {
            "PLAIN_VAR": "plain_value",
        },
    )
    def test_convert_envs_missing_var(self):
        env = ["PLAIN_VAR"]
        env_base64 = ["MISSING_BASE64_VAR"]

        with self.assertRaises(AssertionError) as context:
            convert_envs(env, env_base64)

        self.assertIn(
            "Missing env var MISSING_BASE64_VAR",
            str(context.exception),
        )

    @patch.dict(
        os.environ,
        {
            "DUPLICATE_VAR": "value",
            "DUPLICATE_VAR_BASE64": base64.b64encode(b"value").decode("utf-8"),
        },
    )
    def test_convert_envs_duplicate_var(self):
        env = ["DUPLICATE_VAR"]
        env_base64 = ["DUPLICATE_VAR"]

        with self.assertRaises(AssertionError) as context:
            convert_envs(env, env_base64)

        self.assertIn(
            "Env var DUPLICATE_VAR is already in dict_keys(['DUPLICATE_VAR'])",
            str(context.exception),
        )

    def test_link_static_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "content"))
            with open(os.path.join(temp_dir, "content/file1"), "w") as f:
                f.write("content1")
            with open(os.path.join(temp_dir, "content/file2"), "w") as f:
                f.write("content2")

            links_config = {
                "file1": os.path.join(temp_dir, "file1_link"),
                "file2": os.path.join(temp_dir, "file2_link"),
            }
            link_static_files(
                os.path.join(temp_dir, "content"), links_config, dry_run=False
            )

            self.assertTrue(os.path.islink(os.path.join(temp_dir, "file1_link")))
            self.assertTrue(os.path.islink(os.path.join(temp_dir, "file2_link")))
            with open(os.path.join(temp_dir, "file1_link"), "r") as file:
                self.assertEqual(file.read(), "content1")

    def test_generate_templates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            content_path = temp_dir
            generated_path = os.path.join(temp_dir, "generated")
            os.makedirs(generated_path)
            template_path = os.path.join(content_path, "test/file1.temp")
            os.makedirs(os.path.dirname(template_path))
            with open(template_path, "w") as f:
                f.write("content with {{ TEMP_VAR }}")

            out_path = os.path.join(temp_dir, "file1")
            template_config = {"test/file1.temp": out_path}
            generate_templates(
                content_path,
                template_config,
                env_vars={"TEMP_VAR": "test_value"},
                generated_path=generated_path,
                dry_run=False,
            )

            generated_file_path = os.path.join(generated_path, "test/file1.temp")
            self.assertTrue(os.path.isfile(generated_file_path))
            self.assertTrue(os.path.islink(out_path))
            with open(generated_file_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "content with test_value")
            with open(out_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "content with test_value")

    def test_check_templates_no_diff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            content_path = temp_dir
            generated_path = os.path.join(temp_dir, "generated")
            os.makedirs(generated_path)
            template_path = os.path.join(content_path, "file1.temp")
            generated_file_path = os.path.join(generated_path, "file1.temp")
            with open(template_path, "w") as f:
                f.write("content with {{ TEMP_VAR }}")
            with open(generated_file_path, "w") as f:
                f.write("content with test_value")

            template_config = {"file1.temp": os.path.join(temp_dir, "file1")}
            with patch("sys.stdout", new_callable=StringIO) as out:
                check_templates(
                    content_path,
                    template_config,
                    {"TEMP_VAR": "test_value"},
                    generated_path,
                )
                output = out.getvalue().strip()
                self.assertIn("No differences found", output)

    def test_check_templates_with_diff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            content_path = temp_dir
            generated_path = os.path.join(temp_dir, "generated")
            os.makedirs(generated_path)
            template_path = os.path.join(content_path, "file1.temp")
            generated_file_path = os.path.join(generated_path, "file1.temp")
            with open(template_path, "w") as f:
                f.write("content with {{ TEMP_VAR }}")
            with open(generated_file_path, "w") as f:
                f.write("different content")

            template_config = {"file1.temp": os.path.join(temp_dir, "file1")}
            with patch("sys.stdout", new_callable=StringIO) as out:
                check_templates(
                    content_path,
                    template_config,
                    {"TEMP_VAR": "test_value"},
                    generated_path,
                )
                output = out.getvalue().strip()
                self.assertIn("Differences found", output)


if __name__ == "__main__":
    unittest.main()
