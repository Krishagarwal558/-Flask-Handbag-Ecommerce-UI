const toastRoot = document.querySelector("#toast-root");

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastRoot.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
}

setTheme(localStorage.getItem("theme") || "light");

document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme;
  setTheme(current === "dark" ? "light" : "dark");
});

document.querySelector("[data-nav-toggle]")?.addEventListener("click", () => {
  document.querySelector("[data-nav-links]")?.classList.toggle("open");
});

document.querySelectorAll("[data-wishlist]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    button.classList.toggle("active");
    button.textContent = button.classList.contains("active") ? "♥" : "♡";
    showToast(button.classList.contains("active") ? "Added to wishlist" : "Removed from wishlist");
  });
});

document.querySelectorAll("[data-gallery-thumb]").forEach((button) => {
  button.addEventListener("click", () => {
    const main = document.querySelector("[data-gallery-main]");
    if (main) main.src = button.dataset.galleryThumb;
  });
});

document.querySelectorAll("[data-add-cart]").forEach((button) => {
  button.addEventListener("click", async () => {
    const quantityInput = document.querySelector("[data-product-quantity]");
    const quantity = quantityInput ? Number(quantityInput.value) : 1;
    button.disabled = true;
    try {
      const response = await fetch("/add-to-cart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: button.dataset.productId, quantity }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Could not add item");
      document.querySelectorAll("[data-cart-count]").forEach((node) => {
        node.textContent = data.cart_count;
      });
      showToast(data.message || "Added to cart");
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-cart-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    const response = await fetch("/cart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: button.dataset.productId, action: button.dataset.cartAction }),
    });
    const data = await response.json();
    if (data.ok) {
      showToast("Cart updated");
      window.location.reload();
    }
  });
});

document.querySelector("[data-coupon]")?.addEventListener("click", () => {
  showToast("Coupon endpoint ready to connect");
});

document.querySelectorAll(".ajax-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button[type='submit']");
    if (submit) submit.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: form.method || "POST",
        body: new FormData(form),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Something went wrong");
      showToast(data.message || "Saved successfully");
      if (data.redirect) setTimeout(() => window.location.assign(data.redirect), 500);
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      if (submit) submit.disabled = false;
    }
  });
});

document.querySelectorAll("[data-order-status]").forEach((select) => {
  select.addEventListener("change", async () => {
    const response = await fetch("/admin/order-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: select.dataset.orderId, status: select.value }),
    });
    const data = await response.json();
    showToast(data.message || "Order status updated");
  });
});

document.querySelectorAll("[data-delete-product]").forEach((button) => {
  button.addEventListener("click", async () => {
    const response = await fetch(`/admin/product/${button.dataset.productId}/delete`, { method: "POST" });
    const data = await response.json();
    showToast(data.message || "Handbag delete endpoint ready");
  });
});

const range = document.querySelector("[data-price-range]");
const rangeValue = document.querySelector("[data-price-value]");
if (range && rangeValue) {
  range.addEventListener("input", () => {
    rangeValue.textContent = range.value;
  });
}
