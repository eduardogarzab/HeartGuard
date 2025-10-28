
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Login
    page.goto("http://localhost:8080/login")
    page.fill('input[name="email"]', "admin@heartguard.com")
    page.fill('input[name="password"]', "Admin#2025")
    page.click('button[type="submit"]')
    page.wait_for_url("http://localhost:8080/superadmin/dashboard")

    # Navigate to patient locations and take screenshot
    page.goto("http://localhost:8080/superadmin/locations/patients?patient_id=8c9436b4-f085-405f-a3d2-87cb1d1cf097")
    page.wait_for_selector("#locations-map")
    page.screenshot(path="jules-scratch/verification/patient_locations.png")

    # Navigate to patient detail and take screenshot
    page.goto("http://localhost:8080/superadmin/patients/8c9436b4-f085-405f-a3d2-87cb1d1cf097")
    page.wait_for_selector("#locations-map")
    page.screenshot(path="jules-scratch/verification/patient_detail.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
