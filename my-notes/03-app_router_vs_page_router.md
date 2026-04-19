# App Router vs Page Router : Case Study: E-commerce (Product Page)

Using something like Amazon or Flipkart.

## Page Requirements

`/product/123` needs:

* Product info (fast, critical)
* Reviews (slow, large)
* Recommendations (medium)

---

# 1. Pages Router (how teams used to build it)

## Code

```jsx
// pages/product/[id].js

export async function getServerSideProps({ params }) {
  const product = await fetch(`/api/product/${params.id}`).then(r => r.json());
  const reviews = await fetch(`/api/reviews/${params.id}`).then(r => r.json());
  const recs = await fetch(`/api/recommendations/${params.id}`).then(r => r.json());

  return {
    props: { product, reviews, recs }
  };
}

export default function Page({ product, reviews, recs }) {
  return (
    <>
      <h1>{product.name}</h1>
      <div>{reviews.length} reviews</div>
      <div>{recs.length} recommendations</div>
    </>
  );
}
```

## What actually happens (real system behavior)

1. Request comes in
2. Server waits for:

   * product API
   * reviews API (slow)
   * recommendations API
3. Only after all complete → HTML sent

## Real issue in production

* If reviews API is slow → entire page is slow
* No prioritization of critical vs non-critical data
* Hard to scale when APIs have different latency

---

# 2. App Router (how modern teams build it)

## Code

```jsx
// app/product/[id]/page.js

import { Suspense } from "react";
import Reviews from "./Reviews";
import Recommendations from "./Recommendations";

export default async function Page({ params }) {
  const product = await fetch(`/api/product/${params.id}`).then(r => r.json());

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

```jsx
// app/product/[id]/Reviews.js
export default async function Reviews({ id }) {
  const data = await fetch(`/api/reviews/${id}`).then(r => r.json());
  return <div>{data.length} reviews</div>;
}
```

---

# What actually happens now

1. Request comes in
2. Server fetches **only product (critical)**
3. Sends HTML immediately
4. Reviews + recommendations load **independently (streamed)**

---

# Side-by-side behavior

| Step            | Pages Router | App Router          |
| --------------- | ------------ | ------------------- |
| Product ready   | waits        | renders immediately |
| Reviews slow    | blocks page  | loads later         |
| Recommendations | blocks page  | independent         |
| User sees UI    | late         | early               |

---

# Real production impact

## Pages Router

* TTFB tied to slowest API
* Higher bounce rate
* Over-fetching

## App Router

* Faster first paint
* Lower server load (less blocking)
* Better UX under high latency

---

# The actual reason App Router exists

Not “new syntax”, but to solve this exact problem:

> In real systems, different parts of a page have different latency and importance.

Pages Router cannot model that cleanly.
App Router is built specifically for that.

### Node Js vs Python FastAPI Backend

I’ll keep the same **e-commerce product page** example and show how it connects to:

* Next.js (Node) as backend
  vs
* Python backend (e.g., FastAPI)

---

# 1. Two deployment models

## A. Next.js as full backend (Node server)

Using Next.js server (Node runtime):

```text
Browser → Next.js (Node) → DB / services
```

You fetch data directly inside server components.

---

## B. Next.js frontend + Python backend

Using FastAPI:

```text
Browser → Next.js → FastAPI → DB
```

Next.js becomes a **frontend orchestration layer**, not the main backend.

---

# 2. Pages Router vs App Router impact

## Pages Router + Python backend

```jsx
// pages/product/[id].js

export async function getServerSideProps({ params }) {
  const data = await fetch(`http://fastapi/product/${params.id}`);
  return { props: { data: await data.json() } };
}
```

### Behavior

* One API call per page
* Backend must **aggregate everything**

### FastAPI typically looks like:

```python
# FastAPI
@app.get("/product/{id}")
def get_product(id: int):
    product = get_product_data(id)
    reviews = get_reviews(id)
    recs = get_recommendations(id)

    return {
        "product": product,
        "reviews": reviews,
        "recs": recs
    }
```

### Architecture pattern

* Backend = **fat aggregation layer**
* Frontend = thin

---

## App Router + Python backend

```jsx
// app/product/[id]/page.js

export default async function Page({ params }) {
  const product = await fetch(`http://fastapi/product/${params.id}`).then(r => r.json());

  return (
    <>
      <Product data={product} />
      <Reviews id={params.id} />
      <Recommendations id={params.id} />
    </>
  );
}
```

```jsx
// app/product/[id]/Reviews.js
export default async function Reviews({ id }) {
  const data = await fetch(`http://fastapi/reviews/${id}`).then(r => r.json());
  return <div>{data.length}</div>;
}
```

---

### FastAPI now changes to:

```python
@app.get("/product/{id}")
def product(id: int):
    return get_product_data(id)

@app.get("/reviews/{id}")
def reviews(id: int):
    return get_reviews(id)

@app.get("/recommendations/{id}")
def recs(id: int):
    return get_recommendations(id)
```

---

### Architecture pattern

* Backend = **granular services**
* Frontend = **orchestrator (important shift)**

---

# 3. Key architectural difference

## Pages Router model

```text
Frontend → 1 API → Backend aggregates → Response
```

* Backend owns composition
* Harder to scale independently
* Tight coupling

---

## App Router model

```text
Frontend (server components)
   ├── /product API
   ├── /reviews API
   └── /recommendations API
```

* Frontend composes data
* Backend becomes modular
* Better parallelism

---

# 4. Where Node (Next.js server) fits

## If you use Next.js server as backend

You can skip Python entirely:

```jsx
// inside server component

const product = await db.query(...)
```

### Pros

* Fewer network hops
* Simpler stack
* Good for small–mid systems

### Cons

* Not ideal for:

  * heavy data processing
  * ML pipelines
  * complex data engineering logic

---

## If you use Python backend

Better when you have:

* data pipelines
* ML/recommendation systems
* heavy compute

Which fits your background (data engineering).

---

# 5. Real industry pattern

Most modern systems use **hybrid architecture**:

```text
Browser
   ↓
Next.js (App Router, server components)
   ↓
Python services (FastAPI)
   ↓
Data layer (DB, Spark, etc.)
```

### Why this works best

* Next.js:

  * handles UI composition
  * streaming
  * caching
* Python:

  * handles business logic
  * data processing

---

# 6. Important shift with App Router

This is the key insight:

## Pages Router world

* Backend decides response shape

## App Router world

* Frontend decides composition
* Backend provides **building blocks**

---

# 7. Performance implication

## Pages Router + backend aggregation

* 1 request
* but slow if backend is slow

## App Router + multiple APIs

* multiple parallel requests
* streamed UI
* faster perceived performance

---

# 8. When to choose what

## Use Next.js (Node) as backend if:

* simple CRUD
* low data complexity
* small team

## Use Python backend if:

* heavy data logic (your case)
* ML/recommendations
* large-scale systems

## Use App Router when:

* you want frontend-driven composition
* multiple APIs with different latency

---

# Final mental model

* Pages Router → “Backend builds the page”

* App Router → “Frontend assembles the page from services”

* Node-only → “Fullstack JS app”

* Next.js + Python → “Frontend + data platform separation”
