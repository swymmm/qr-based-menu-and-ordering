# Food Mall QR Ordering (Rebuilt)

## Quick start

1. Recreate the database and tables:
   ```
   python database.py
   ```
2. Seed sample outlets, items, tables, and admin user:
   ```
   python insert_data.py
   ```
3. Run the app:
   ```
   python app.py
   ```

## Demo credentials

- Admin login: `admin / admin`
- Outlet login: password is `outlet`

## Guest flow

1. Scan a table QR (example: `/?table=5`).
2. Choose an outlet on the welcome page.
3. Add items to cart, checkout with mock payment.
4. Track status on the live status page.

## Admin flow

- Login at `/admin/login` to add/toggle outlets and menu items.

## Notes

- QR images are stored in `static/qr/` after running `generate_qr.py`.
- This is a demo mock-payment flow (no real gateway integration).
