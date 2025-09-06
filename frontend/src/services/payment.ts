import { authService } from './auth';

// Define the API base URL at the top of the file
const API_BASE_URL = 'http://api-gateway:8080/api/v1';

interface PaymentCreate {
  booking_id: string; // UUID string
  payment_method_id: string; // UUID string 
  amount: number;
  currency: string;
  description?: string;
  metadata?: Record<string, any>;
}

interface PaymentResponse {
  id: string;
  booking_id: string;
  payment_method_id: string;
  amount: number;
  currency: string;
  status: string;
  description?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface PaymentMethod {
  id: string; // This should be a UUID from your API
  name: string;
  type: string;
  description: string;
  is_active: boolean;
}

export interface CreatePaymentMethodData {
  method_type: 'CREDIT_CARD' | 'BANK_TRANSFER' | 'DIGITAL_WALLET';
  provider: string;
  card_last_four?: string;
  card_expiry?: string;
  billing_details: Record<string, any>;
}

class PaymentService {
  private baseUrl = `${API_BASE_URL}/payments/`;

  async createPayment(data: PaymentCreate): Promise<PaymentResponse> {
    const token = authService.getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    console.log('Payment service - sending data:', data);

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      console.log('Payment service - response status:', response.status);

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          console.log('Payment service - error response:', errorData);
          
          if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((err: any) => {
                if (typeof err === 'string') return err;
                if (err.msg && err.loc) return `${err.loc.join('.')}: ${err.msg}`;
                return JSON.stringify(err);
              }).join(', ');
            } else {
              errorMessage = JSON.stringify(errorData.detail);
            }
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
          const textResponse = await response.text().catch(() => 'Unknown error');
          errorMessage = `${errorMessage} - ${textResponse}`;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Payment service - success response:', result);
      return result;

    } catch (error) {
      console.error('Payment service - request failed:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to create payment - network or parsing error');
    }
  }

  async createPaymentMethod(data: CreatePaymentMethodData) {
    const token = authService.getToken();
    
    try {
      const response = await fetch(`${API_BASE_URL}/payment-methods/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.log('Payment method service - error response:', errorData);
        throw new Error(errorData.detail || 'Payment method creation failed');
      }

      return await response.json();
    } catch (error) {
      console.log('Payment method service - request failed:', error);
      throw error;
    }
  }

  // Get payment methods from your API instead of mock data
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const token = authService.getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/payment-methods`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        return response.json();
      } else {
        // Fallback to mock data if endpoint doesn't exist yet
        console.warn('Payment methods endpoint not available, using mock data');
        return this.getMockPaymentMethods();
      }
    } catch (error) {
      console.warn('Failed to fetch payment methods, using mock data:', error);
      return this.getMockPaymentMethods();
    }
  }

  private getMockPaymentMethods(): PaymentMethod[] {
    // Generate mock UUIDs for development - replace with real UUIDs from your API
    return [
      {
        id: '11111111-1111-1111-1111-111111111111',
        name: 'Credit/Debit Card',
        type: 'card',
        description: 'Visa, Mastercard, American Express',
        is_active: true
      },
      {
        id: '22222222-2222-2222-2222-222222222222',
        name: 'Bank Transfer',
        type: 'bank',
        description: 'Direct bank transfer',
        is_active: true
      },
      {
        id: '33333333-3333-3333-3333-333333333333',
        name: 'Digital Wallet',
        type: 'wallet',
        description: 'PayPal, Apple Pay, Google Pay',
        is_active: true
      }
    ];
  }

  async getPayment(paymentId: string): Promise<PaymentResponse> {
    const token = authService.getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE_URL}/payments/${paymentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Payment fetch failed' }));
      throw new Error(errorData.detail || errorData.message || 'Failed to fetch payment');
    }

    return response.json();
  }
}

export const paymentService = new PaymentService();