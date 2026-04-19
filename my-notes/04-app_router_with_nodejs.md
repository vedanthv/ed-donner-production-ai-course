## App Router with NodeJS

---

# 1. Architecture (Node backend + App Router)

Using Next.js as both frontend and backend:

```text
Browser
  ↓
Next.js (App Router, server components)
  ↓
Route Handlers / external services / DB
```

You can:

* call internal APIs (Next.js route handlers)
* call external services
* query DB directly

---

# 2. Example: Product Page with Multiple APIs

## Folder structure

```bash
/app
  product/[id]/
    page.js
    Reviews.js
    Recommendations.js
/api
  product/[id]/route.js
  reviews/[id]/route.js
  recommendations/[id]/route.js
```

---

# 3. Backend APIs (Node via Next.js Route Handlers)

These replace a traditional backend like Express.

```js
// app/api/product/[id]/route.js

export async function GET(req, { params }) {
  const product = await getProductFromDB(params.id);
  return Response.json(product);
}
```

```js
// app/api/reviews/[id]/route.js

export async function GET(req, { params }) {
  const reviews = await getReviews(params.id);
  return Response.json(reviews);
}
```

---

# 4. App Router (multiple API calls, cleanly split)

```jsx
// app/product/[id]/page.js

import { Suspense } from "react";
import Reviews from "./Reviews";
import Recommendations from "./Recommendations";

export default async function Page({ params }) {
  const product = await fetch(`http://localhost:3000/api/product/${params.id}`)
    .then(r => r.json());

  return (
    <>
      <h1>{product.name}</h1>

      <Suspense fallback={<div>Loading reviews...</div>}>
        <Reviews id={params.id} />
      </Suspense>

      <Suspense fallback={<div>Loading recommendations...</div>}>
        <Recommendations id={params.id} />
      </Suspense>
    </>
  );
}
```

---

## Independent API calls per component

```jsx
// app/product/[id]/Reviews.js

export default async function Reviews({ id }) {
  const data = await fetch(`http://localhost:3000/api/reviews/${id}`)
    .then(r => r.json());

  return <div>{data.length} reviews</div>;
}
```

---

# 5. What’s happening under the hood

* `page.js` fetches product (critical)
* `Reviews` and `Recommendations`:

  * run in parallel
  * fetch their own APIs
* UI streams progressively

So yes:

* multiple API calls
* parallel execution
* no blocking

---

# 6. Important optimization (very important)

If you’re calling your own backend from server components:

## Better approach (avoid HTTP overhead)

Instead of:

```js
await fetch("http://localhost:3000/api/product/123")
```

Do this:

```js
import { getProduct } from "@/lib/product";

const product = await getProduct(params.id);
```

### Why

* avoids network call
* faster (direct function call)
* same runtime (Node)

---

# 7. When to use APIs vs direct calls

## Use direct function calls if:

* same codebase
* same runtime (Node)
* internal logic

## Use API calls if:

* microservices
* different services (Python, Go, etc.)
* external systems

---

# 8. Real industry pattern (Node-only stack)

```text
Next.js App Router
   ├── Server Components (UI + orchestration)
   ├── Route Handlers (API layer)
   └── DB / services
```

* No separate backend needed
* Clean separation inside same repo

---

# 9. Key takeaway

Yes, and more importantly:

* App Router is designed for **multiple independent data sources**
* Node backend (Next.js) supports this natively
* You can:

  * call many APIs
  * fetch in parallel
  * stream UI

---

# 10. One subtle but critical point

Even though you *can* make many API calls:

* Don’t blindly create 10+ API calls per page
* Group logically when needed
* Use caching (`fetch` caching in Next.js)
