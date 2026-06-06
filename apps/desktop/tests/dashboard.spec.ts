import { test, expect } from "@playwright/test";

test("desktop shell renders core navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("LKP Command Layer")).toBeVisible();
});
