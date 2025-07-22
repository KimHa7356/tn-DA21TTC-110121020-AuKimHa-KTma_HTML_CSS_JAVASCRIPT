import js from "@eslint/js";
import globals from "globals";
import stylistic from "@stylistic/eslint-plugin-js";
import html from "eslint-plugin-html"; // Thêm plugin HTML

export default [
  {
    files: ["**/*.js"],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.browser,
      },
      ecmaVersion: 2020,
      sourceType: "module",
    },
    plugins: {
      "@stylistic/js": stylistic,
    },
    rules: {
      ...js.configs.recommended.rules,
      "@stylistic/js/semi": ["error", "always"],
      "no-console": "off",
      eqeqeq: "error",
      "no-unused-vars": [
        "warn",
        { vars: "all", args: "none", ignoreRestSiblings: false },
      ],
      "no-undef": "error",
    },
    settings: {
      "working-directory": process.cwd(),
    },
  },
  {
    files: ["**/*.html"], // Áp dụng cho file HTML
    plugins: {
      html: html,
    },
    settings: {
      "html/html-extensions": [".html"], // Đảm bảo xử lý file .html
      "html/javascript": true, // Bật phân tích JavaScript trong thẻ <script>
    },
  },
];
