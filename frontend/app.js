// Конфигурация API
const API_BASE = '/api';

// Состояние приложения
let state = {
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user')) || null,
  currentDate: new Date().toISOString().split('T')[0],
  foods: [],
  categories: [],
  meals: [],
  summary: null
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  initDateInput();
  if (state.token && state.user) {
    showMainApp();
  } else {
    showAuth();
  }
});

function initDateInput() {
  const dateInput = document.getElementById('diary-date');
  if (dateInput) {
    dateInput.value = state.currentDate;
    dateInput.addEventListener('change', (e) => {
      state.currentDate = e.target.value;
      loadDiaryData();
    });
  }
}

function setupEventListeners() {
  // Переключение вкладок авторизации
  document.getElementById('tab-login').addEventListener('click', () => switchAuthTab('login'));
  document.getElementById('tab-register').addEventListener('click', () => switchAuthTab('register'));

  // Сабмит логина
  document.getElementById('form-login').addEventListener('submit', handleLogin);
  // Сабмит регистрации
  document.getElementById('form-register').addEventListener('submit', handleRegister);

  // Выход
  document.getElementById('btn-logout').addEventListener('click', logout);

  // Изменение суточной цели
  document.getElementById('btn-edit-target').addEventListener('click', promptChangeTarget);

  // Кнопка "Сегодня"
  document.getElementById('btn-today').addEventListener('click', () => {
    state.currentDate = new Date().toISOString().split('T')[0];
    document.getElementById('diary-date').value = state.currentDate;
    loadDiaryData();
  });

  // Навигация по главным вкладкам
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      const btn = e.currentTarget;
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add('active');
      }

      if (targetId === 'tab-diary') loadDiaryData();
      if (targetId === 'tab-foods') loadFoodsData();
      if (targetId === 'tab-admin') loadAdminData();
    });
  });

  // Модальные окна
  document.getElementById('btn-open-add-meal').addEventListener('click', openAddMealModal);
  document.getElementById('btn-open-add-food').addEventListener('click', openAddFoodModal);
  document.getElementById('form-meal').addEventListener('submit', handleSaveMeal);
  document.getElementById('form-food').addEventListener('submit', handleSaveFood);

  // Поиск и фильтрация продуктов
  document.getElementById('food-search-input').addEventListener('input', debounce(loadFoodsData, 300));
  document.getElementById('food-category-filter').addEventListener('change', loadFoodsData);
}

// Быстрое заполнение учетных данных
window.fillCredentials = function(username, password) {
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = password;
};

// Переключение табов авторизации
function switchAuthTab(type) {
  const tabLogin = document.getElementById('tab-login');
  const tabReg = document.getElementById('tab-register');
  const formLogin = document.getElementById('form-login');
  const formReg = document.getElementById('form-register');

  if (type === 'login') {
    tabLogin.classList.add('active');
    tabReg.classList.remove('active');
    formLogin.classList.remove('hidden');
    formReg.classList.add('hidden');
  } else {
    tabReg.classList.add('active');
    tabLogin.classList.remove('active');
    formReg.classList.remove('hidden');
    formLogin.classList.add('hidden');
  }
}

// Запросы к API
async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const options = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (res.status === 401) {
      logout();
      throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
    }
    if (res.status === 204) {
      return null;
    }
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Ошибка выполнения запроса');
    }
    return data;
  } catch (err) {
    alert(err.message);
    throw err;
  }
}

// Авторизация
async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await apiRequest('/auth/login', 'POST', { username, password });
    state.token = res.access_token;
    state.user = res.user;
    localStorage.setItem('token', state.token);
    localStorage.setItem('user', JSON.stringify(state.user));
    showMainApp();
  } catch (err) {
    console.error(err);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById('reg-username').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const role = document.getElementById('reg-role').value;
  const target = parseInt(document.getElementById('reg-target').value) || 2000;

  try {
    await apiRequest('/auth/register', 'POST', {
      username,
      email,
      password,
      role,
      daily_calorie_target: target
    });
    alert('Аккаунт успешно создан! Теперь выполните вход.');
    switchAuthTab('login');
    document.getElementById('login-username').value = username;
    document.getElementById('login-password').value = password;
  } catch (err) {
    console.error(err);
  }
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  showAuth();
}

function showAuth() {
  document.getElementById('auth-section').classList.remove('hidden');
  document.getElementById('main-section').classList.add('hidden');
  document.getElementById('nav-user-panel').classList.add('hidden');
}

function showMainApp() {
  document.getElementById('auth-section').classList.add('hidden');
  document.getElementById('main-section').classList.remove('hidden');
  document.getElementById('nav-user-panel').classList.remove('hidden');

  document.getElementById('nav-username').textContent = state.user.username;
  const roleBadge = document.getElementById('nav-role-badge');
  roleBadge.textContent = state.user.role === 'admin' ? 'Администратор' : 'Пользователь';
  roleBadge.className = `badge ${state.user.role === 'admin' ? 'badge-admin' : 'badge-client'}`;
  document.getElementById('nav-target-cal').textContent = state.user.daily_calorie_target;

  // Показываем админскую вкладку только администраторам
  if (state.user.role === 'admin') {
    document.getElementById('nav-tab-admin').classList.remove('hidden');
  } else {
    document.getElementById('nav-tab-admin').classList.add('hidden');
  }

  loadDiaryData();
}

async function promptChangeTarget() {
  const current = state.user.daily_calorie_target || 2000;
  const val = prompt('Укажите новую суточную норму калорий (ккал):', current);
  if (!val) return;
  const newTarget = parseInt(val);
  if (isNaN(newTarget) || newTarget < 500 || newTarget > 10000) {
    alert('Пожалуйста, укажите число от 500 до 10000');
    return;
  }

  try {
    const updated = await apiRequest(`/auth/target?target=${newTarget}`, 'PUT');
    state.user.daily_calorie_target = updated.daily_calorie_target;
    localStorage.setItem('user', JSON.stringify(state.user));
    document.getElementById('nav-target-cal').textContent = updated.daily_calorie_target;
    loadDiaryData();
  } catch (err) {
    console.error(err);
  }
}

// --- РАБОТА С ДНЕВНИКОМ ПИТАНИЯ ---
async function loadDiaryData() {
  try {
    const [summary, meals] = await Promise.all([
      apiRequest(`/meals/summary?target_date=${state.currentDate}`),
      apiRequest(`/meals/?target_date=${state.currentDate}`)
    ]);
    state.summary = summary;
    state.meals = meals;
    renderSummary();
    renderMeals();
  } catch (err) {
    console.error(err);
  }
}

function renderSummary() {
  if (!state.summary) return;
  const s = state.summary;
  document.getElementById('sum-consumed').textContent = s.consumed_calories;
  document.getElementById('sum-target').textContent = s.target_calories;
  document.getElementById('sum-remaining').textContent = `Осталось: ${s.remaining_calories} ккал`;
  document.getElementById('sum-proteins').textContent = `${s.total_proteins} г`;
  document.getElementById('sum-fats').textContent = `${s.total_fats} г`;
  document.getElementById('sum-carbs').textContent = `${s.total_carbs} г`;

  const percent = Math.min(100, Math.round((s.consumed_calories / s.target_calories) * 100));
  const fill = document.getElementById('calorie-progress-fill');
  fill.style.width = `${percent}%`;
  fill.style.backgroundColor = percent > 100 ? '#ef4444' : '#10b981';
}

const MEAL_TYPE_NAMES = {
  breakfast: 'Завтрак',
  lunch: 'Обед',
  dinner: 'Ужин',
  snack: 'Перекус'
};

function renderMeals() {
  const container = document.getElementById('meals-list');
  container.innerHTML = '';

  if (state.meals.length === 0) {
    container.innerHTML = '<div class="empty-state"><p style="color:#64748b; text-align:center; padding:2rem;">В этот день еще нет записей о приемах пищи. Нажмите «+ Добавить прием пищи».</p></div>';
    return;
  }

  const groups = { breakfast: [], lunch: [], dinner: [], snack: [] };
  state.meals.forEach(m => {
    if (groups[m.meal_type]) groups[m.meal_type].push(m);
  });

  Object.entries(groups).forEach(([type, items]) => {
    if (items.length === 0) return;

    const groupTotalCal = items.reduce((acc, i) => acc + i.portion_calories, 0);

    const card = document.createElement('div');
    card.className = 'meal-group-card';
    card.innerHTML = `
      <div class="meal-group-header">
        <span>${MEAL_TYPE_NAMES[type]} (${items.length})</span>
        <span style="color:#059669">${Math.round(groupTotalCal)} ккал</span>
      </div>
      <div class="meal-group-items">
        ${items.map(i => `
          <div class="meal-item-row">
            <div class="meal-item-info">
              <h4>${escapeHtml(i.food.name)}</h4>
              <span class="meal-item-sub">${i.weight_grams} г ${i.note ? `• ${escapeHtml(i.note)}` : ''}</span>
            </div>
            <div class="meal-item-macros">
              <span class="macro-tag" style="color:#059669">${i.portion_calories} ккал</span>
              <span class="macro-tag" style="color:#2563eb; font-size:0.8rem;">Б: ${i.portion_proteins}г</span>
              <span class="macro-tag" style="color:#d97706; font-size:0.8rem;">Ж: ${i.portion_fats}г</span>
              <span class="macro-tag" style="color:#059669; font-size:0.8rem;">У: ${i.portion_carbs}г</span>
              <div class="action-btns">
                <button class="btn btn-sm btn-outline" onclick="editMealEntry(${i.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteMealEntry(${i.id})">🗑️</button>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(card);
  });
}

// Модальное окно записи приема пищи
async function openAddMealModal() {
  document.getElementById('modal-meal-title').textContent = 'Добавить прием пищи';
  document.getElementById('meal-edit-id').value = '';
  document.getElementById('meal-weight-input').value = '100';
  document.getElementById('meal-note-input').value = '';

  await loadFoodsForSelect();
  openModal('modal-meal');
}

async function loadFoodsForSelect() {
  const foods = await apiRequest('/foods/');
  state.foods = foods;
  const select = document.getElementById('meal-food-select');
  select.innerHTML = foods.map(f => `
    <option value="${f.id}">${escapeHtml(f.name)} (${f.calories} ккал / 100г)</option>
  `).join('');
}

window.editMealEntry = async function(id) {
  const meal = state.meals.find(m => m.id === id);
  if (!meal) return;

  await loadFoodsForSelect();
  document.getElementById('modal-meal-title').textContent = 'Редактировать запись';
  document.getElementById('meal-edit-id').value = meal.id;
  document.getElementById('meal-type-select').value = meal.meal_type;
  document.getElementById('meal-food-select').value = meal.food_id;
  document.getElementById('meal-weight-input').value = meal.weight_grams;
  document.getElementById('meal-note-input').value = meal.note || '';

  openModal('modal-meal');
};

async function handleSaveMeal(e) {
  e.preventDefault();
  const editId = document.getElementById('meal-edit-id').value;
  const payload = {
    food_id: parseInt(document.getElementById('meal-food-select').value),
    meal_type: document.getElementById('meal-type-select').value,
    weight_grams: parseFloat(document.getElementById('meal-weight-input').value),
    note: document.getElementById('meal-note-input').value.trim() || null
  };

  try {
    if (editId) {
      await apiRequest(`/meals/${editId}`, 'PUT', payload);
    } else {
      // Подставляем текущую дату дневника
      payload.consumed_at = `${state.currentDate}T12:00:00`;
      await apiRequest('/meals/', 'POST', payload);
    }
    closeModal('modal-meal');
    loadDiaryData();
  } catch (err) {
    console.error(err);
  }
}

window.deleteMealEntry = async function(id) {
  if (!confirm('Удалить эту запись из дневника?')) return;
  try {
    await apiRequest(`/meals/${id}`, 'DELETE');
    loadDiaryData();
  } catch (err) {
    console.error(err);
  }
};

// --- РАБОТА СО СПРАВОЧНИКОМ ПРОДУКТОВ ---
async function loadFoodsData() {
  const query = document.getElementById('food-search-input').value.trim();
  const category = document.getElementById('food-category-filter').value;

  let url = '/foods/?';
  if (query) url += `q=${encodeURIComponent(query)}&`;
  if (category && category !== 'Все') url += `category=${encodeURIComponent(category)}&`;

  try {
    const [foods, categories] = await Promise.all([
      apiRequest(url),
      apiRequest('/foods/categories')
    ]);
    state.foods = foods;
    state.categories = categories;

    renderCategoryOptions();
    renderFoodsTable();
  } catch (err) {
    console.error(err);
  }
}

function renderCategoryOptions() {
  const filter = document.getElementById('food-category-filter');
  const currentVal = filter.value;
  filter.innerHTML = '<option value="Все">Все категории</option>' + 
    state.categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
  if (state.categories.includes(currentVal)) {
    filter.value = currentVal;
  }
}

function renderFoodsTable() {
  const tbody = document.getElementById('foods-table-body');
  tbody.innerHTML = '';

  if (state.foods.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:1.5rem; color:#64748b;">Продукты не найдены</td></tr>';
    return;
  }

  state.foods.forEach(f => {
    const isOwner = f.created_by_id === state.user.id;
    const isAdmin = state.user.role === 'admin';
    const canEdit = isAdmin || (isOwner && !f.is_verified);
    const canDelete = isAdmin || isOwner;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><b>${escapeHtml(f.name)}</b></td>
      <td><span class="badge badge-user">${escapeHtml(f.category || 'Общее')}</span></td>
      <td><b>${f.calories}</b></td>
      <td style="color:#2563eb">${f.proteins}</td>
      <td style="color:#d97706">${f.fats}</td>
      <td style="color:#059669">${f.carbs}</td>
      <td>
        ${f.is_verified 
          ? '<span class="badge badge-verified">✓ Проверен</span>' 
          : '<span class="badge badge-user">Пользовательский</span>'}
      </td>
      <td>
        <div class="action-btns">
          ${canEdit ? `<button class="btn btn-sm btn-outline" onclick="editFoodItem(${f.id})">✏️</button>` : ''}
          ${canDelete ? `<button class="btn btn-sm btn-danger" onclick="deleteFoodItem(${f.id})">🗑️</button>` : ''}
          ${!canEdit && !canDelete ? '<span style="color:#94a3b8; font-size:0.8rem;">Только чтение</span>' : ''}
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openAddFoodModal() {
  document.getElementById('modal-food-title').textContent = 'Новый продукт';
  document.getElementById('food-edit-id').value = '';
  document.getElementById('food-name').value = '';
  document.getElementById('food-category').value = '';
  document.getElementById('food-calories').value = '';
  document.getElementById('food-proteins').value = '';
  document.getElementById('food-fats').value = '';
  document.getElementById('food-carbs').value = '';

  const adminGroup = document.getElementById('admin-verify-group');
  if (state.user.role === 'admin') {
    adminGroup.classList.remove('hidden');
    document.getElementById('food-is-verified').checked = true;
  } else {
    adminGroup.classList.add('hidden');
  }

  openModal('modal-food');
}

window.editFoodItem = function(id) {
  const food = state.foods.find(f => f.id === id);
  if (!food) return;

  document.getElementById('modal-food-title').textContent = 'Редактировать продукт';
  document.getElementById('food-edit-id').value = food.id;
  document.getElementById('food-name').value = food.name;
  document.getElementById('food-category').value = food.category || '';
  document.getElementById('food-calories').value = food.calories;
  document.getElementById('food-proteins').value = food.proteins;
  document.getElementById('food-fats').value = food.fats;
  document.getElementById('food-carbs').value = food.carbs;

  const adminGroup = document.getElementById('admin-verify-group');
  if (state.user.role === 'admin') {
    adminGroup.classList.remove('hidden');
    document.getElementById('food-is-verified').checked = food.is_verified;
  } else {
    adminGroup.classList.add('hidden');
  }

  openModal('modal-food');
};

async function handleSaveFood(e) {
  e.preventDefault();
  const editId = document.getElementById('food-edit-id').value;
  const payload = {
    name: document.getElementById('food-name').value.trim(),
    category: document.getElementById('food-category').value.trim() || 'Общее',
    calories: parseFloat(document.getElementById('food-calories').value),
    proteins: parseFloat(document.getElementById('food-proteins').value) || 0.0,
    fats: parseFloat(document.getElementById('food-fats').value) || 0.0,
    carbs: parseFloat(document.getElementById('food-carbs').value) || 0.0
  };

  if (state.user.role === 'admin') {
    payload.is_verified = document.getElementById('food-is-verified').checked;
  }

  try {
    if (editId) {
      await apiRequest(`/foods/${editId}`, 'PUT', payload);
    } else {
      await apiRequest('/foods/', 'POST', payload);
    }
    closeModal('modal-food');
    loadFoodsData();
  } catch (err) {
    console.error(err);
  }
}

window.deleteFoodItem = async function(id) {
  if (!confirm('Вы действительно хотите удалить этот продукт?')) return;
  try {
    await apiRequest(`/foods/${id}`, 'DELETE');
    loadFoodsData();
  } catch (err) {
    console.error(err);
  }
};

// --- АДМИН ПАНЕЛЬ ---
async function loadAdminData() {
  if (state.user.role !== 'admin') return;
  try {
    const list = await apiRequest('/meals/admin/all');
    const tbody = document.getElementById('admin-table-body');
    tbody.innerHTML = '';
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:1.5rem; color:#64748b;">Логов активности нет</td></tr>';
      return;
    }
    list.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${item.id}</td>
        <td><b>User #${item.user_id}</b></td>
        <td>${escapeHtml(item.food.name)}</td>
        <td><span class="badge badge-user">${MEAL_TYPE_NAMES[item.meal_type] || item.meal_type}</span></td>
        <td>${item.weight_grams} г</td>
        <td><b>${item.portion_calories} ккал</b></td>
        <td>${new Date(item.consumed_at).toLocaleString('ru-RU')}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

// Вспомогательные утилиты
window.openModal = function(id) {
  document.getElementById(id).classList.remove('hidden');
};

window.closeModal = function(id) {
  document.getElementById(id).classList.add('hidden');
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function debounce(fn, delay) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), delay);
  };
}
