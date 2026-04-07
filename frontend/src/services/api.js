const API_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;

const getHeaders = (token) => ({
  'Content-Type': 'application/json',
  ...(token && { 'Authorization': `Bearer ${token}` })
});

const handleResponse = async (response) => {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Error en la solicitud');
  }
  return data;
};

// Habitaciones
export const getHabitaciones = async (token, params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/habitaciones?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getHabitacion = async (token, id) => {
  const response = await fetch(`${API_URL}/api/habitaciones/${id}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getDisponibilidad = async (token, params) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/habitaciones/disponibilidad?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getTiposHabitacion = async (token) => {
  const response = await fetch(`${API_URL}/api/habitaciones/tipos`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const updateHabitacion = async (token, id, data) => {
  const response = await fetch(`${API_URL}/api/habitaciones/${id}`, {
    method: 'PUT',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

// Reservas
export const getReservas = async (token, params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/reservas?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getReserva = async (token, id) => {
  const response = await fetch(`${API_URL}/api/reservas/${id}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const buscarReserva = async (token, params) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/reservas/buscar?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const createReserva = async (token, data) => {
  const response = await fetch(`${API_URL}/api/reservas`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateReserva = async (token, id, data) => {
  const response = await fetch(`${API_URL}/api/reservas/${id}`, {
    method: 'PUT',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const cancelarReserva = async (token, id, motivo) => {
  const response = await fetch(`${API_URL}/api/reservas/${id}/cancelar`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify({ motivo })
  });
  return handleResponse(response);
};

// Check-in / Check-out
export const processCheckin = async (token, data) => {
  const response = await fetch(`${API_URL}/api/checkin`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const processCheckout = async (token, data) => {
  const response = await fetch(`${API_URL}/api/checkout`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const getConsumos = async (token, reservaId) => {
  const response = await fetch(`${API_URL}/api/consumos/${reservaId}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const addConsumo = async (token, data) => {
  const response = await fetch(`${API_URL}/api/consumos`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

// Pagos
export const getPagos = async (token, params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/pagos?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const createPago = async (token, data) => {
  const response = await fetch(`${API_URL}/api/pagos`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

// Facturas
export const getFacturas = async (token, params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/facturas?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getFactura = async (token, id) => {
  const response = await fetch(`${API_URL}/api/facturas/${id}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

// Reportes
export const getDashboard = async (token) => {
  const response = await fetch(`${API_URL}/api/reportes/dashboard`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const getReporteOcupacion = async (token, fechaInicio, fechaFin) => {
  const response = await fetch(
    `${API_URL}/api/reportes/ocupacion?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`,
    { headers: getHeaders(token) }
  );
  return handleResponse(response);
};

export const getTopClientes = async (token, limite = 10) => {
  const response = await fetch(`${API_URL}/api/reportes/top-clientes?limite=${limite}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

// Usuarios
export const getUsuarios = async (token, params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_URL}/api/usuarios?${query}`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

export const createUsuario = async (token, data) => {
  const response = await fetch(`${API_URL}/api/usuarios`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateUsuario = async (token, id, data) => {
  const response = await fetch(`${API_URL}/api/usuarios/${id}`, {
    method: 'PUT',
    headers: getHeaders(token),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const deleteUsuario = async (token, id) => {
  const response = await fetch(`${API_URL}/api/usuarios/${id}`, {
    method: 'DELETE',
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

// Servicios adicionales
export const getServiciosAdicionales = async (token) => {
  const response = await fetch(`${API_URL}/api/servicios-adicionales`, {
    headers: getHeaders(token)
  });
  return handleResponse(response);
};

// Health
export const getHealth = async () => {
  const response = await fetch(`${API_URL}/api/health`);
  return handleResponse(response);
};
