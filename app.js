const expenseCategories = [
  'Compras',
  'Roupa',
  'Casa',
  'Carro',
  'Imprevistos',
  'Condomínio',
  'Luz',
  'Internet',
  'Celular',
  'Gasolina',
  'Mercado',
  'Ifood',
  'Saídas'
];

const incomeCategories = ['Salário João', 'Salário Emily', 'Extra', 'Rendimento', 'Outro'];
const defaultAccounts = [
  { id: 'bb-joao', name: 'Banco do Brasil - João', balance: 0 },
  { id: 'bb-emily', name: 'Banco do Brasil Emily', balance: 0 },
  { id: 'itau', name: 'Itaú', balance: 0 },
  { id: 'viacredi', name: 'Viacredi', balance: 0 },
  { id: 'caju', name: 'Caju', balance: 0 }
];

const typeSelect = document.getElementById('type');
const categorySelect = document.getElementById('category');
const transactionForm = document.getElementById('transaction-form');
const transactionAccountSelect = document.getElementById('transaction-account');
const periodInput = document.getElementById('period');
const transactionsList = document.getElementById('transactions-list');
const incomeTotalEl = document.getElementById('income-total');
const expenseTotalEl = document.getElementById('expense-total');
const balanceTotalEl = document.getElementById('balance-total');
const accountsTotalEl = document.getElementById('accounts-total');
const netWorthEl = document.getElementById('net-worth');
const clearDataButton = document.getElementById('clear-data');
const barChart = document.getElementById('bar-chart');
const donutChart = document.getElementById('donut-chart');
const legendEl = document.getElementById('legend');
const investmentForm = document.getElementById('investment-form');
const investmentSelect = document.getElementById('investment-select');
const investMoreForm = document.getElementById('invest-more-form');
const investmentsList = document.getElementById('investments-list');
const accountForm = document.getElementById('account-form');
const accountSelect = document.getElementById('account-select');
const accountOperationSelect = document.getElementById('account-operation');
const accountsList = document.getElementById('accounts-list');

const storageKey = 'finances-state-v2';

const defaultState = {
  transactions: [],
  investments: [],
  accounts: defaultAccounts.map((account) => ({ ...account })),
  period: new Date().toISOString().slice(0, 7)
};

let state = loadState();

function loadState() {
  const stored = localStorage.getItem(storageKey);
  if (!stored) {
    return {
      ...defaultState,
      accounts: defaultAccounts.map((account) => ({ ...account }))
    };
  }

  try {
    const parsed = JSON.parse(stored);
    return {
      transactions: Array.isArray(parsed.transactions) ? parsed.transactions : [],
      investments: Array.isArray(parsed.investments) ? parsed.investments : [],
      accounts: Array.isArray(parsed.accounts) && parsed.accounts.length
        ? parsed.accounts.map((account) => ({
            id: account.id || account.name,
            name: account.name,
            balance: Number(account.balance) || 0
          }))
        : defaultAccounts.map((account) => ({ ...account })),
      period: parsed.period || defaultState.period
    };
  } catch (error) {
    console.error('Falha ao carregar estado', error);
    return {
      ...defaultState,
      accounts: defaultAccounts.map((account) => ({ ...account }))
    };
  }
}

function saveState() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
}

function updateCategoryOptions() {
  const categories = typeSelect.value === 'expense' ? expenseCategories : incomeCategories;
  categorySelect.innerHTML = categories
    .map((category) => `<option value="${category}">${category}</option>`)
    .join('');
}

function renderAccountOptions() {
  const options = state.accounts
    .map((account) => `<option value="${account.id}">${account.name}</option>`)
    .join('');

  transactionAccountSelect.innerHTML = `<option value="">Sem conta</option>${options}`;
  accountSelect.innerHTML = options;
}

function setDefaultDate() {
  const dateInput = document.getElementById('date');
  if (!dateInput.value) {
    dateInput.value = new Date().toISOString().slice(0, 10);
  }
}

function initialize() {
  periodInput.value = state.period;
  updateCategoryOptions();
  renderAccountOptions();
  setDefaultDate();
  render();
  bindEvents();
}

function bindEvents() {
  typeSelect.addEventListener('change', updateCategoryOptions);
  periodInput.addEventListener('change', (event) => {
    state.period = event.target.value;
    saveState();
    render();
  });

  transactionForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const accountId = transactionAccountSelect.value;
    const payload = {
      id: crypto.randomUUID(),
      type: typeSelect.value,
      category: categorySelect.value,
      description: document.getElementById('description').value.trim(),
      amount: Number(document.getElementById('amount').value),
      date: document.getElementById('date').value,
      month: state.period,
      accountId: accountId || null,
      accountName: accountId ? state.accounts.find((account) => account.id === accountId)?.name || null : null
    };

    if (!payload.description || Number.isNaN(payload.amount) || payload.amount <= 0) {
      return;
    }

    if (payload.type === 'expense' && payload.accountId) {
      const account = state.accounts.find((item) => item.id === payload.accountId);
      if (account) {
        account.balance -= payload.amount;
      }
    }

    if (payload.type === 'income' && payload.accountId) {
      const account = state.accounts.find((item) => item.id === payload.accountId);
      if (account) {
        account.balance += payload.amount;
      }
    }

    state.transactions.unshift(payload);
    saveState();
    transactionForm.reset();
    setDefaultDate();
    updateCategoryOptions();
    renderAccountOptions();
    render();
  });

  accountForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const accountId = accountSelect.value;
    const operation = accountOperationSelect.value;
    const amount = Number(document.getElementById('account-amount').value);
    const description = document.getElementById('account-description').value.trim();

    if (!accountId || Number.isNaN(amount) || amount < 0) {
      return;
    }

    const account = state.accounts.find((item) => item.id === accountId);
    if (!account) {
      return;
    }

    if (operation === 'set') {
      account.balance = amount;
    } else if (operation === 'add') {
      account.balance += amount;
    } else {
      account.balance -= amount;
    }

    if (description) {
      state.transactions.unshift({
        id: crypto.randomUUID(),
        type: 'income',
        category: 'Ajuste',
        description,
        amount: operation === 'subtract' ? 0 : amount,
        date: new Date().toISOString().slice(0, 10),
        month: state.period,
        accountId,
        accountName: account.name
      });
    }

    saveState();
    accountForm.reset();
    render();
  });

  investmentForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const payload = {
      id: crypto.randomUUID(),
      name: document.getElementById('investment-name').value.trim(),
      amount: Number(document.getElementById('investment-amount').value),
      location: document.getElementById('investment-location').value.trim() || 'Sem local informado'
    };

    if (!payload.name || Number.isNaN(payload.amount) || payload.amount < 0) {
      return;
    }

    state.investments.push(payload);
    saveState();
    investmentForm.reset();
    render();
  });

  investMoreForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const selectedId = investmentSelect.value;
    const amount = Number(document.getElementById('extra-amount').value);
    if (!selectedId || Number.isNaN(amount) || amount <= 0) {
      return;
    }

    state.investments = state.investments.map((investment) =>
      investment.id === selectedId ? { ...investment, amount: investment.amount + amount } : investment
    );

    saveState();
    investMoreForm.reset();
    render();
  });

  clearDataButton.addEventListener('click', () => {
    const confirmed = window.confirm('Deseja apagar todos os dados salvos?');
    if (!confirmed) return;

    state = {
      ...defaultState,
      period: state.period,
      accounts: defaultAccounts.map((account) => ({ ...account }))
    };
    localStorage.removeItem(storageKey);
    render();
  });
}

function removeTransaction(id) {
  const transaction = state.transactions.find((item) => item.id === id);
  if (transaction?.accountId) {
    const account = state.accounts.find((item) => item.id === transaction.accountId);
    if (account) {
      if (transaction.type === 'expense') {
        account.balance += transaction.amount;
      } else if (transaction.type === 'income') {
        account.balance -= transaction.amount;
      }
    }
  }

  state.transactions = state.transactions.filter((item) => item.id !== id);
  saveState();
  render();
}

function removeInvestment(id) {
  state.investments = state.investments.filter((investment) => investment.id !== id);
  saveState();
  render();
}

function render() {
  const currentTransactions = state.transactions.filter((transaction) => transaction.month === state.period);
  const income = currentTransactions
    .filter((transaction) => transaction.type === 'income')
    .reduce((acc, item) => acc + item.amount, 0);
  const expenses = currentTransactions
    .filter((transaction) => transaction.type === 'expense')
    .reduce((acc, item) => acc + item.amount, 0);
  const balance = income - expenses;
  const accountsTotal = state.accounts.reduce((acc, item) => acc + item.balance, 0);
  const investedValue = state.investments.reduce((acc, item) => acc + item.amount, 0);
  const netWorth = accountsTotal + investedValue;

  incomeTotalEl.textContent = formatCurrency(income);
  expenseTotalEl.textContent = formatCurrency(expenses);
  balanceTotalEl.textContent = formatCurrency(balance);
  accountsTotalEl.textContent = formatCurrency(accountsTotal);
  netWorthEl.textContent = formatCurrency(netWorth);

  renderTransactions(currentTransactions);
  renderAccounts();
  renderInvestments();
  renderBarChart(income, expenses);
  renderDonutChart(currentTransactions.filter((item) => item.type === 'expense'));
  renderInvestmentSelect();
}

function renderTransactions(transactions) {
  if (transactions.length === 0) {
    transactionsList.innerHTML = '<li class="empty-state">Nenhuma movimentação para este período ainda.</li>';
    return;
  }

  transactionsList.innerHTML = transactions
    .map(
      (transaction) => `
        <li class="transaction-item">
          <div class="transaction-meta">
            <strong>${transaction.description}</strong>
            <span>${transaction.category} • ${transaction.date}${transaction.accountName ? ` • ${transaction.accountName}` : ''}</span>
          </div>
          <div class="transaction-amount ${transaction.type === 'income' ? 'income' : 'expense'}">
            ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
          </div>
          <button class="remove-btn" type="button" data-remove-transaction="${transaction.id}">Remover</button>
        </li>
      `
    )
    .join('');

  document.querySelectorAll('[data-remove-transaction]').forEach((button) => {
    button.addEventListener('click', () => removeTransaction(button.getAttribute('data-remove-transaction')));
  });
}

function renderAccounts() {
  if (state.accounts.length === 0) {
    accountsList.innerHTML = '<div class="empty-state">Nenhuma conta cadastrada.</div>';
    return;
  }

  accountsList.innerHTML = state.accounts
    .map(
      (account) => `
        <div class="account-item">
          <div>
            <strong>${account.name}</strong>
            <div>${account.balance < 0 ? 'Saldo negativo' : 'Saldo disponível'}</div>
          </div>
          <div class="account-balance ${account.balance < 0 ? 'negative' : ''}">${formatCurrency(account.balance)}</div>
        </div>
      `
    )
    .join('');
}

function renderInvestments() {
  if (state.investments.length === 0) {
    investmentsList.innerHTML = '<div class="empty-state">Nenhum investimento cadastrado.</div>';
    return;
  }

  investmentsList.innerHTML = state.investments
    .map(
      (investment) => `
        <div class="investment-item">
          <div>
            <strong>${investment.name}</strong>
            <div>${investment.location}</div>
          </div>
          <div>${formatCurrency(investment.amount)}</div>
          <button class="remove-btn" type="button" data-remove-investment="${investment.id}">Remover</button>
        </div>
      `
    )
    .join('');

  document.querySelectorAll('[data-remove-investment]').forEach((button) => {
    button.addEventListener('click', () => removeInvestment(button.getAttribute('data-remove-investment')));
  });
}

function renderInvestmentSelect() {
  investmentSelect.innerHTML = state.investments
    .map((investment) => `<option value="${investment.id}">${investment.name} — ${formatCurrency(investment.amount)}</option>`)
    .join('');

  if (state.investments.length === 0) {
    investmentSelect.innerHTML = '<option value="">Cadastre um investimento primeiro</option>';
  }
}

function renderBarChart(income, expenses) {
  const max = Math.max(income, expenses, 1);
  const barWidth = 80;
  const gap = 40;
  const left = 50;
  const heights = [income / max * 140, expenses / max * 140];
  const labels = ['Ganhos', 'Gastos'];
  const colors = ['#41c7ae', '#ff6987'];

  barChart.innerHTML = `
    <rect x="0" y="0" width="320" height="220" rx="18" fill="transparent"></rect>
    ${labels
      .map((label, index) => {
        const x = left + index * (barWidth + gap);
        const y = 180 - heights[index];
        return `
          <rect x="${x}" y="${y}" width="${barWidth}" height="${heights[index]}" rx="10" fill="${colors[index]}"></rect>
          <text x="${x + barWidth / 2}" y="200" text-anchor="middle" fill="#93a7c9" font-size="11">${label}</text>
          <text x="${x + barWidth / 2}" y="${y - 8}" text-anchor="middle" fill="#f3f7ff" font-size="11">${formatCurrency(index === 0 ? income : expenses)}</text>
        `;
      })
      .join('')}
  `;
}

function renderDonutChart(expenses) {
  const total = expenses.reduce((acc, item) => acc + item.amount, 0);
  if (total === 0) {
    donutChart.innerHTML = `
      <circle cx="110" cy="110" r="70" fill="none" stroke="#16263b" stroke-width="38"></circle>
      <text x="110" y="112" text-anchor="middle" fill="#93a7c9">Sem dados</text>
    `;
    legendEl.innerHTML = '';
    return;
  }

  const categories = expenses.reduce((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + item.amount;
    return acc;
  }, {});

  const colors = ['#41c7ae', '#6f7cff', '#ff6987', '#ffbe5c', '#5dc9ff', '#e36dff', '#8df0c8'];
  const entries = Object.entries(categories);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;
  const segments = entries
    .map(([name, value], index) => {
      const segmentLength = (value / total) * circumference;
      const strokeDasharray = `${segmentLength} ${circumference - segmentLength}`;
      const strokeDashoffset = -offset;
      offset += segmentLength;
      return `<circle cx="110" cy="110" r="70" fill="none" stroke="${colors[index % colors.length]}" stroke-width="38" stroke-linecap="round" stroke-dasharray="${strokeDasharray}" stroke-dashoffset="${strokeDashoffset}" transform="rotate(-90 110 110)"></circle>`;
    })
    .join('');

  donutChart.innerHTML = `
    <circle cx="110" cy="110" r="70" fill="none" stroke="#16263b" stroke-width="38"></circle>
    ${segments}
    <text x="110" y="105" text-anchor="middle" fill="#f3f7ff" font-size="16">${formatCurrency(total)}</text>
    <text x="110" y="126" text-anchor="middle" fill="#93a7c9" font-size="11">Gastos</text>
  `;

  legendEl.innerHTML = entries
    .map(([name, value], index) => `
      <div class="legend-item">
        <span><span class="legend-badge" style="background:${colors[index % colors.length]}"></span>${name}</span>
        <strong>${formatCurrency(value)}</strong>
      </div>
    `)
    .join('');
}

initialize();
