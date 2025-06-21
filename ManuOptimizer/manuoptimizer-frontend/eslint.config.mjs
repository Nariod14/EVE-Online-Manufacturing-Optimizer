import storybook from "eslint-plugin-storybook";
import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  ...storybook.configs["flat/recommended"],

  // Disable rules globally
  {
    rules: {
      "react/no-unescaped-entities": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // Optionally, disable only for specific files (e.g., stories)
  {
    files: ["**/*.stories.@(ts|tsx|js|jsx|mjs|cjs)"],
    rules: {
      "storybook/default-exports": "off",
      // Add other Storybook-specific rules to disable here
    },
  },
];

export default eslintConfig;
