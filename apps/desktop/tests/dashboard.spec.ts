import { test, expect } from "@playwright/test";

test("desktop shell renders core navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("LKP Command Layer")).toBeVisible();
});

test("developer operator can open task intake", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("jarvis-operator-index", "2");
  });
  await page.goto("/#tasks");
  await expect(page.getByRole("heading", { name: "Create Task" })).toBeVisible();
  await expect(page.getByLabel("Request")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create Task" })).toBeVisible();
});

test("finance operator can capture memory", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("jarvis-operator-index", "3");
  });
  await page.goto("/#memory");
  await expect(page.getByRole("heading", { name: "Capture Memory" })).toBeVisible();
  await expect(page.getByLabel("Memory Value")).toBeVisible();
  await expect(page.getByRole("button", { name: "Capture Memory" })).toBeVisible();
});
