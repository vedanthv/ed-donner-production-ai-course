
# Big Picture

* **Props** → data passed *into* a component (read-only)
* **State** → data *owned by* a component (mutable)
* **`useState`** → hook to create/manage state
* **`useEffect`** → hook to run side effects (API calls, timers, etc.)

---

#  1. Props (inputs to a component)

Props are like function arguments.

```jsx
function Greeting(props) {
  return <h1>Hello, {props.name}</h1>;
}
```

Usage:

```jsx
<Greeting name="Vedanth" />
```

### Key points:

* Passed from parent → child
* **Immutable (read-only)**
* Used for configuration / data flow

---

#  2. State (internal data)

State is data that **belongs to the component** and can change.

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  return <h1>{count}</h1>;
}
```

### Key points:

* Local to component
* Changes trigger re-render
* Mutable via setter function

---

#  3. `useState` (how you create state)

```jsx
const [count, setCount] = useState(0);
```

### Breakdown:

* `count` → current value
* `setCount` → function to update it
* `0` → initial value

---

### Example with interaction:

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Clicked {count} times
    </button>
  );
}
```

---

#  4. `useEffect` (side effects)

Used when something happens **outside rendering**, like:

* API calls
* Timers
* Subscriptions

---

## Basic example:

```jsx
import { useEffect } from "react";

useEffect(() => {
  console.log("Component mounted");
}, []);
```

### What `[]` means:

* Run **only once** (on mount)

---

## Run when state changes:

```jsx
useEffect(() => {
  console.log("Count changed:", count);
}, [count]);
```

---

## Cleanup example:

```jsx
useEffect(() => {
  const timer = setInterval(() => {
    console.log("Running...");
  }, 1000);

  return () => clearInterval(timer);
}, []);
```

---

#  How they work together

```jsx
function App() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log("Count updated:", count);
  }, [count]);

  return (
    <Child count={count} setCount={setCount} />
  );
}

function Child({ count, setCount }) {
  return (
    <button onClick={() => setCount(count + 1)}>
      {count}
    </button>
  );
}
```

Here’s the same explanation, clean and without emojis.

---

# High-level idea

* `App` owns the state (`count`)
* `Child` receives that state and a function to update it
* `useEffect` runs whenever `count` changes

This is the standard React pattern: **parent manages state, child consumes it**

---

# Step-by-step execution

## 1. Initial render

```jsx
const [count, setCount] = useState(0);
```

* `count = 0`
* `setCount` is the updater function

---

## 2. useEffect setup

```jsx
useEffect(() => {
  console.log("Count updated:", count);
}, [count]);
```

Meaning:

* Runs after the component renders
* Runs again whenever `count` changes

On first render:

```
Count updated: 0
```

---

## 3. Rendering Child

```jsx
<Child count={count} setCount={setCount} />
```

You pass:

* `count` (data)
* `setCount` (function to update data)

---

# Inside Child

```jsx
function Child({ count, setCount }) {
```

This is destructuring props. Equivalent to:

```jsx
props.count
props.setCount
```

---

## Button behavior

```jsx
<button onClick={() => setCount(count + 1)}>
```

On click:

* Takes current `count`
* Adds 1
* Calls `setCount`

---

# What happens on click

## First click

1. Button click:

```jsx
setCount(0 + 1)
```

2. State updates:

```
count = 1
```

3. React re-renders `App`

4. `useEffect` runs:

```
Count updated: 1
```

---

## Second click

Same sequence:

```
count = 2 → re-render → useEffect runs
```

---

# Data flow (important)

```
App (state owner)
   ↓ props
Child (uses state)
   ↓ event
setCount()
   ↑
App updates state
```

This is called **unidirectional data flow**.

---

# Key concepts demonstrated

## 1. State is owned by parent

```jsx
const [count, setCount] = useState(0);
```

The source of truth is in `App`.

---

## 2. Props pass data down

```jsx
<Child count={count} />
```

Child cannot modify `count` directly.

---

## 3. Functions allow child to update state

```jsx
setCount={setCount}
```

Child calls this to request an update.

---

## 4. useEffect reacts to changes

```jsx
[count]
```

Effect runs whenever `count` changes.

---

# Important detail

Instead of:

```jsx
setCount(count + 1)
```

Prefer:

```jsx
setCount(prev => prev + 1)
```

Reason:

* Prevents stale values in async or batched updates

---

# Mental model

* `App` owns and controls the data
* `Child` displays and interacts with it
* Updates flow upward via functions
* Rendering flows downward via props

---

# Final summary

* `useState` creates and manages state
* Props pass state to child components
* Child triggers updates using passed functions
* `useEffect` runs after render when dependencies change
* Every state update triggers a re-render

---

#  Mental Model

Think of a React component like:

```text
Props → Inputs (from parent)
State → Memory (inside component)
useState → Tool to manage memory
useEffect → Tool to react to changes / side effects
```

---

# ⚠️ Common mistakes

###  Modifying props

```jsx
props.name = "New"; //  wrong
```

---

###  Direct state mutation

```jsx
count = count + 1; //  wrong
```

 Correct:

```jsx
setCount(count + 1);
```

---

###  Missing dependencies in useEffect

```jsx
useEffect(() => {
  console.log(count);
}, []); //  count not included
```

---

#  Quick summary table

| Concept   | Purpose                  | Mutable? | Scope          |
| --------- | ------------------------ | -------- | -------------- |
| Props     | Input data               |  No     | Parent → Child |
| State     | Internal data            |  Yes    | Component      |
| useState  | Manage state             | —        | Component      |
| useEffect | Side effects / lifecycle | —        | Component      |