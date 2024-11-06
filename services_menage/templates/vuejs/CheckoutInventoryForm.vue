
<template>
  <div class="checkout-inventory-form">
    <h2>Checkout Inventory</h2>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="cleanliness">Cleanliness (1-5):</label>
        <input v-model.number="form.cleanliness" type="number" id="cleanliness" min="1" max="5" required>
      </div>
      
      <div class="form-group">
        <label for="damages">Damages:</label>
        <textarea v-model="form.damages" id="damages"></textarea>
      </div>
      
      <div class="form-group">
        <label for="missing_items">Missing Items:</label>
        <textarea v-model="form.missing_items" id="missing_items"></textarea>
      </div>
      
      <div class="form-group">
        <label for="additional_notes">Additional Notes:</label>
        <textarea v-model="form.additional_notes" id="additional_notes"></textarea>
      </div>
      
      <button type="submit" :disabled="isSubmitting">Submit</button>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'CheckoutInventoryForm',
  props: {
    reservationId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      form: {
        reservation: this.reservationId,
        cleanliness: 5,
        damages: '',
        missing_items: '',
        additional_notes: ''
      },
      isSubmitting: false
    };
  },
  methods: {
    async submitForm() {
      this.isSubmitting = true;
      try {
        const response = await axios.post('/api/checkout-inventory/', this.form);
        console.log('Inventory submitted successfully:', response.data);
        // Vous pouvez émettre un événement ici pour informer le composant parent
        this.$emit('inventory-submitted', response.data);
      } catch (error) {
        console.error('Error submitting inventory:', error);
        // Gérer l'erreur (afficher un message à l'utilisateur, etc.)
      } finally {
        this.isSubmitting = false;
      }
    }
  }
}
</script>

<style scoped>
.checkout-inventory-form {
  max-width: 500px;
  margin: 0 auto;
}
.form-group {
  margin-bottom: 15px;
}
label {
  display: block;
  margin-bottom: 5px;
}
input, textarea {
  width: 100%;
  padding: 8px;
}
button {
  padding: 10px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  cursor: pointer;
}
button:disabled {
  background-color: #cccccc;
}
</style>