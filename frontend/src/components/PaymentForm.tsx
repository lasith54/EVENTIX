import React, { useState } from 'react';
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js';

interface PaymentFormProps {
  booking: any;
  onSuccess: (paymentIntent: any) => void;
  onError: (error: string) => void;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ booking, onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success`,
        },
        redirect: 'if_required',
      });

      if (error) {
        console.error('Payment failed:', error);
        setErrorMessage(error.message || 'Payment failed');
        onError(error.message || 'Payment failed');
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        console.log('Payment succeeded:', paymentIntent);
        onSuccess(paymentIntent);
      }
    } catch (err) {
      console.error('Payment processing error:', err);
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setErrorMessage(message);
      onError(message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-display font-semibold text-foreground mb-6">
        Payment Details
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <PaymentElement 
            options={{
              layout: 'tabs',
            }}
          />
        </div>

        {errorMessage && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
            <p className="text-sm">{errorMessage}</p>
          </div>
        )}

        <div className="space-y-4">
          <div className="text-xs text-muted-foreground">
            <p>💳 Your payment is secured with industry-standard encryption</p>
            <p>🔒 We never store your payment information</p>
            <p>📧 You'll receive a confirmation email after payment</p>
          </div>

          <button
            type="submit"
            disabled={!stripe || isProcessing}
            className="w-full bg-primary text-primary-foreground py-3 px-4 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isProcessing ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing Payment...
              </div>
            ) : (
              `Pay ${booking.currency} ${booking.total_amount.toFixed(2)}`
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PaymentForm;