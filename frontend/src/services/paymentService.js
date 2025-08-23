import api from './api';

export const paymentService = {
  createPayment: (paymentData) => api.post('/payments', paymentData),
  getPaymentMethods: () => api.get('/payment-methods'),
  addPaymentMethod: (methodData) => api.post('/payment-methods', methodData),
  processRefund: (paymentId, refundData) => api.post(`/payments/${paymentId}/refund`, refundData),
};