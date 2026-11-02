import { defineConfig } from "vitest/config";

// Unit tests for the pure logic (lib/, moves helpers). They live in test/, outside
// src/, so the Remotion bundle never sees them.
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    environment: "node",
  },
});
