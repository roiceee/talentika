import { defineConfig } from "@hey-api/openapi-ts";
import "dotenv/config";

export default defineConfig({
  input: `${process.env.BACKEND_URL}/swagger.json/`,
  output: "src/lib/client",
  plugins: [
    { name: "@hey-api/client-axios", runtimeConfigPath: "../hey-api" },
    "@hey-api/typescript",
    "@hey-api/sdk",
  ],
});
