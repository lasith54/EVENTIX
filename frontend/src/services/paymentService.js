import api from './api';

export const paymentService = {
  createPayment: (paymentData) => api.post('/api/v1/payments', paymentData),
  getPaymentMethods: () => api.get('/api/v1/payment-methods'),
  addPaymentMethod: (methodData) => api.post('/api/v1/payment-methods', methodData),
  processRefund: (paymentId, refundData) => api.post(`/api/v1/refunds/payments/${paymentId}/refund`, refundData),
};