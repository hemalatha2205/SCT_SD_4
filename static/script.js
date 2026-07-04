const form = document.getElementById('scrape-form');
const urlInput = document.getElementById('url');
const sampleSelector = document.getElementById('sample-selector');
const messageArea = document.getElementById('message-area');
const productsBody = document.getElementById('products-body');
const searchInput = document.getElementById('search-input');
const filterCategory = document.getElementById('filter-category');
const filterRating = document.getElementById('filter-rating');
const filterPrice = document.getElementById('filter-price');
const refreshButton = document.getElementById('refresh-btn');

let products = [
  {
    name: 'The Midnight Library',
    price: '£12.00',
    price_value: 12,
    rating: '4★',
    image: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=300&q=80',
    category: 'Fiction'
  },
  {
    name: 'Atomic Habits',
    price: '£14.99',
    price_value: 14.99,
    rating: '5★',
    image: 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=300&q=80',
    category: 'Self-Help'
  },
  {
    name: 'Sapiens',
    price: '£16.50',
    price_value: 16.5,
    rating: '4★',
    image: 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=300&q=80',
    category: 'History'
  }
];
let filteredProducts = [];

function setMessage(text, isError = false) {
  messageArea.textContent = text;
  messageArea.style.color = isError ? '#ff5d7a' : '#ffb84d';
}

function updateStats(stats) {
  const safeStats = stats || {
    total_products: products.length,
    average_price: 0,
    highest_price: 0,
    lowest_price: 0,
    categories: 0
  };

  document.getElementById('total-products').textContent = safeStats.total_products;
  document.getElementById('average-price').textContent = `£${Number(safeStats.average_price || 0).toFixed(2)}`;
  document.getElementById('highest-price').textContent = `£${Number(safeStats.highest_price || 0).toFixed(2)}`;
  document.getElementById('lowest-price').textContent = `£${Number(safeStats.lowest_price || 0).toFixed(2)}`;
  document.getElementById('categories').textContent = safeStats.categories;
}

function populateCategoryOptions() {
  const categories = [...new Set(products.map((item) => item.category).filter(Boolean))];
  filterCategory.innerHTML = '<option value="all">All Categories</option>';
  categories.forEach((category) => {
    const option = document.createElement('option');
    option.value = category;
    option.textContent = category;
    filterCategory.appendChild(option);
  });
}

function renderProducts() {
  const searchValue = searchInput.value.trim().toLowerCase();
  const categoryValue = filterCategory.value;
  const ratingValue = filterRating.value;
  const priceValue = filterPrice.value;

  filteredProducts = products.filter((product) => {
    const matchesSearch = product.name.toLowerCase().includes(searchValue);
    const matchesCategory = categoryValue === 'all' || product.category === categoryValue;
    const matchesRating = ratingValue === 'all' || product.rating === ratingValue;
    let matchesPrice = true;
    if (priceValue === 'under-15') matchesPrice = product.price_value < 15;
    if (priceValue === '15-25') matchesPrice = product.price_value >= 15 && product.price_value <= 25;
    if (priceValue === 'above-25') matchesPrice = product.price_value > 25;
    return matchesSearch && matchesCategory && matchesRating && matchesPrice;
  });

  productsBody.innerHTML = '';
  if (!filteredProducts.length) {
    productsBody.innerHTML = '<tr><td colspan="5">No products match the current filters.</td></tr>';
    return;
  }

  filteredProducts.forEach((product) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.price}</td>
      <td>${product.rating}</td>
      <td>${product.category}</td>
      <td>${product.image ? `<img src="${product.image}" alt="${product.name}" />` : '—'}</td>
    `;
    productsBody.appendChild(row);
  });
}

function toggleLoading(isLoading) {
  const spinner = form.querySelector('.spinner');
  const label = form.querySelector('.btn-label');
  const button = form.querySelector('button');
  button.disabled = isLoading;
  label.hidden = isLoading;
  spinner.hidden = !isLoading;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const url = urlInput.value.trim() || sampleSelector.value;
  toggleLoading(true);
  setMessage('Scraping in progress...');

  try {
    const response = await fetch('/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ url })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Unexpected error');
    }

    products = data.products;
    updateStats(data.stats);
    populateCategoryOptions();
    renderProducts();
    setMessage(data.message);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    toggleLoading(false);
  }
});

sampleSelector.addEventListener('change', () => {
  urlInput.value = sampleSelector.value;
});

searchInput.addEventListener('input', renderProducts);
filterCategory.addEventListener('change', renderProducts);
filterRating.addEventListener('change', renderProducts);
filterPrice.addEventListener('change', renderProducts);
refreshButton.addEventListener('click', () => {
  searchInput.value = '';
  filterCategory.value = 'all';
  filterRating.value = 'all';
  filterPrice.value = 'all';
  renderProducts();
});

populateCategoryOptions();
updateStats({
  total_products: products.length,
  average_price: products.reduce((sum, item) => sum + Number(item.price_value || 0), 0) / products.length,
  highest_price: Math.max(...products.map((item) => Number(item.price_value || 0))),
  lowest_price: Math.min(...products.map((item) => Number(item.price_value || 0))),
  categories: [...new Set(products.map((item) => item.category))].length
});
renderProducts();
