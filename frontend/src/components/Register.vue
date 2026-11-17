
<script setup>
import { ref } from 'vue'

const emit = defineEmits(['registration-success'])

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

const error = ref('')
const success = ref('')
const loading = ref(false)

async function register() {
  error.value = ''
  success.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }

  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }

  loading.value = true

  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        name: name.value.trim(),
        email: email.value.trim(),
        password: password.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.message || 'Registration failed.'
      return
    }

    success.value = 'Registration successful! You can now log in.'

    name.value = ''
    email.value = ''
    password.value = ''
    confirmPassword.value = ''

  } catch (err) {
    error.value = 'Cannot connect to the server.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container my-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow border-0">
          <div class="card-body p-4">

            <h2 class="text-center text-success mb-4">
              Create Account
            </h2>

            <div
              v-if="error"
              class="alert alert-danger"
              role="alert"
            >
              {{ error }}
            </div>

            <div
              v-if="success"
              class="alert alert-success"
              role="status"
            >
              {{ success }}

              <button
                class="btn btn-success btn-sm d-block mt-3"
                @click="emit('registration-success')"
              >
                Go to Login
              </button>
            </div>

            <form @submit.prevent="register">

              <div class="mb-3">
                <label for="registerName" class="form-label">
                  Full Name
                </label>

                <input
                  id="registerName"
                  v-model="name"
                  type="text"
                  class="form-control"
                  placeholder="Enter your full name"
                  maxlength="100"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="registerEmail" class="form-label">
                  Email Address
                </label>

                <input
                  id="registerEmail"
                  v-model="email"
                  type="email"
                  class="form-control"
                  placeholder="Enter your email"
                  maxlength="120"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="registerPassword" class="form-label">
                  Password
                </label>

                <input
                  id="registerPassword"
                  v-model="password"
                  type="password"
                  class="form-control"
                  placeholder="Create a password"
                  minlength="6"
                  autocomplete="new-password"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="confirmPassword" class="form-label">
                  Confirm Password
                </label>

                <input
                  id="confirmPassword"
                  v-model="confirmPassword"
                  type="password"
                  class="form-control"
                  placeholder="Confirm your password"
                  minlength="6"
                  autocomplete="new-password"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-success w-100"
                :disabled="loading"
              >
                {{ loading ? 'Registering...' : 'Register' }}
              </button>

            </form>

            <p class="text-center mt-3 mb-0">
              Already have an account?

              <a
                href="#"
                class="text-success"
                @click.prevent="emit('registration-success')"
              >
                Login
              </a>
            </p>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>
