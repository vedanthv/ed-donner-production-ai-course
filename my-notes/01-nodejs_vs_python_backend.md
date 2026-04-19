Let’s take a simple online store and compare how it works **before (Vercel SSR)** vs **after (your static export + FastAPI setup)**.

---

# Example: Product Page (`/product/123`)

## BEFORE (Vercel + SSR)

```text
User opens /product/123
→ Request goes to Next.js server
→ Server fetches product data
→ Server renders HTML
→ Sends fully ready page to browser
```

### What happens under the hood:

```ts
export async function getServerSideProps(context) {
  const product = await fetchProduct(context.params.id)

  return {
    props: { product }
  }
}
```

Every request:

* Fresh data
* Server does the work

---

## AFTER (Static export + FastAPI)

```text
Build time:
→ Next.js creates static HTML (no product data)

Runtime:
→ Browser loads page
→ React fetches product from FastAPI
→ UI updates
```

---

# What the code looks like now

## Static page (Next.js)

```jsx
import { useEffect, useState } from "react";

export default function ProductPage() {
  const [product, setProduct] = useState(null);

  useEffect(() => {
    fetch("http://your-fastapi/api/product/123")
      .then(res => res.json())
      .then(setProduct);
  }, []);

  if (!product) return <p>Loading...</p>;

  return <h1>{product.name}</h1>;
}
```

---

## Backend (FastAPI)

```python
@app.get("/api/product/{id}")
def get_product(id: str):
    return {
        "id": id,
        "name": "iPhone 15",
        "price": 999
    }
```

---

# Side-by-side behavior

## Product Page

| Feature       | Vercel (SSR)             | Static + FastAPI        |
| ------------- | ------------------------ | ----------------------- |
| Page load     | Fully rendered HTML      | Empty → then loads data |
| Data fetching | Server-side              | Client-side (useEffect) |
| Speed         | Slight delay per request | Faster initial load     |
| Infra         | Node server needed       | Static + Python backend |

---

# Another example: Product Listing Page

## BEFORE (SSR)

```text
User → server → fetch products → render HTML → send
```

---

## AFTER (Static)

```text
User → loads HTML
→ React calls API
→ products appear
```

---

# Checkout flow (important)

## BEFORE:

* Next.js API routes handle payment

## AFTER:

* FastAPI handles payment APIs

```text
Frontend → FastAPI → Payment gateway
```

---

# What actually changed

### Before:

Next.js = full backend + frontend

### After:

Next.js = UI only
FastAPI = backend

---

# Real trade-offs (important in ecommerce)

## Downsides of static export

* Initial page shows loading state
* SEO slightly worse (no pre-rendered product data)
* Dynamic routes (`/product/[id]`) need workaround

---

## Upsides

* Much simpler deployment on AWS
* Faster static file delivery
* Clear separation of concerns

---

# Real-world approach

Most ecommerce platforms use a hybrid approach:

* Product pages → SSR or pre-rendered
* Dashboard/cart → client-side

---

# Final mental model

```text
Frontend (Next.js static)
   ↓
API calls
   ↓
Backend (FastAPI)
   ↓
Database
```
