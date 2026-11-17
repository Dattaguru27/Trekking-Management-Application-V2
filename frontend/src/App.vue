


<script setup>
import { ref, onMounted } from 'vue'
import Login from './components/Login.vue'
import Register from './components/Register.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import ManageTreks from './components/ManageTreks.vue'
import ManageStaff from './components/ManageStaff.vue'
import ManageUsers from './components/ManageUsers.vue'
import StaffDashboard from './components/StaffDashboard.vue'
import UserDashboard from './components/UserDashboard.vue'
import MyBookings from './components/MyBookings.vue'
import UserProfile from './components/UserProfile.vue'
import AdminBookings from './components/AdminBookings.vue'

const currentPage = ref('home')
const loggedInRole = ref('')
const checkingSession = ref(true)
const loggingOut = ref(false)
const authError = ref('')

function dashboardForRole(role) {
  if (role === 'admin') return 'admin-dashboard'
  if (role === 'staff') return 'staff-dashboard'
  if (role === 'user') return 'user-dashboard'
  return 'home'
}

function changePage(page) {
  authError.value = ''

  
const dashboards = {
  'admin-dashboard': 'admin',
  'manage-treks': 'admin',
  'manage-staff': 'admin',
  'manage-users': 'admin',
  'view-bookings': 'admin',
  'staff-dashboard': 'staff',
  'user-dashboard': 'user',
  'my-bookings': 'user',
  'user-profile': 'user'
}


  // Prevent opening another role's dashboard
  if (
    dashboards[page] &&
    dashboards[page] !== loggedInRole.value
  ) {
    return
  }

  // Logged-in users should use their dashboard
  // instead of opening Login or Register.
  if (
    loggedInRole.value &&
    ['login', 'register'].includes(page)
  ) {
    currentPage.value = dashboardForRole(loggedInRole.value)
    return
  }

  currentPage.value = page
}

function handleLoginSuccess(role) {
  loggedInRole.value = role
  authError.value = ''
  currentPage.value = dashboardForRole(role)
}

async function restoreSession() {
  checkingSession.value = true

  try {
    const response = await fetch('/api/auth/me', {
      credentials: 'same-origin'
    })

    if (!response.ok) {
      loggedInRole.value = ''
      currentPage.value = 'home'
      return
    }

    const data = await response.json()

    // Supports the response formats used in Step 37
    const role = data.user?.role ?? data.role

    if (['admin', 'staff', 'user'].includes(role)) {
      loggedInRole.value = role
      currentPage.value = dashboardForRole(role)
    } else {
      loggedInRole.value = ''
      currentPage.value = 'home'
    }

  } catch (error) {
    loggedInRole.value = ''
    currentPage.value = 'home'
    authError.value = 'Unable to check your login session.'
  } finally {
    checkingSession.value = false
  }
}

async function logout() {
  if (loggingOut.value) return

  loggingOut.value = true
  authError.value = ''

  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'same-origin'
    })

    if (!response.ok) {
      throw new Error('Logout failed.')
    }

    loggedInRole.value = ''
    currentPage.value = 'home'

  } catch (error) {
    authError.value = 'Logout failed. Please try again.'
  } finally {
    loggingOut.value = false
  }
}

// Runs when the Vue application first loads
onMounted(() => {
  restoreSession()
})
</script>




<template>
  <div v-if="checkingSession" class="container text-center my-5">
    <div class="spinner-border text-success" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>

    <p class="mt-3">Checking your session...</p>
  </div>

  <div v-else>
    <div
      v-if="authError"
      class="alert alert-danger text-center m-3"
      role="alert"
    >
      {{ authError }}
    </div>

    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
      <div class="container">
        <a
          class="navbar-brand fw-bold"
          href="#"
          @click.prevent="changePage('home')"
        >
          🏔️ Trekking Management
        </a>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarMenu"
          aria-controls="navbarMenu"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarMenu">
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <a
                class="nav-link"
                href="#"
                @click.prevent="changePage('home')"
              >
                Home
              </a>
            </li>

            <li class="nav-item">
              <a
                class="nav-link"
                href="#"
                @click.prevent="changePage('about')"
              >
                About
              </a>
            </li>

            <li v-if="!loggedInRole" class="nav-item">
              <a
                class="nav-link"
                href="#"
                @click.prevent="changePage('login')"
              >
                Login
              </a>
            </li>

            <li v-if="!loggedInRole" class="nav-item">
              <a
                class="nav-link"
                href="#"
                @click.prevent="changePage('register')"
              >
                Register
              </a>
            </li>

<!-- Dashboard Link -->
<li v-if="loggedInRole" class="nav-item">
  <a
    class="nav-link"
    href="#"
    @click.prevent="changePage(dashboardForRole(loggedInRole))"
  >
    Dashboard
  </a>
</li>

<!-- Logout Button -->
<li v-if="loggedInRole" class="nav-item ms-lg-2">
  <button
    class="btn btn-outline-light"
    type="button"
    :disabled="loggingOut"
    @click="logout"
  >
    {{ loggingOut ? 'Logging out...' : 'Logout' }}
  </button>
</li>

          </ul>
        </div>
      </div>
    </nav>

    <!-- Home Page -->
    <div v-if="currentPage === 'home'">
      <section class="hero text-center text-white">
        <div class="container">
          <h1 class="display-4 fw-bold">
            Explore the Mountains
          </h1>

          <p class="lead mt-3">
            Discover amazing trekking adventures,
            book your favorite treks, and create memories.
          </p>

          <button
            class="btn btn-light btn-lg mt-3"
            @click="changePage('register')"
          >
            Get Started
          </button>
        </div>
      </section>

      <section class="container my-5">
        <h2 class="text-center mb-4">
          Why Choose Our Trekking Platform?
        </h2>

        <div class="row g-4">
          <div class="col-md-4">
            <div class="card h-100 shadow-sm text-center">
              <div class="card-body">
                <h3>🏔️</h3>
                <h5 class="card-title">Explore Treks</h5>
                <p class="card-text">
                  Discover treks at different locations
                  and difficulty levels.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 shadow-sm text-center">
              <div class="card-body">
                <h3>📅</h3>
                <h5 class="card-title">Easy Booking</h5>
                <p class="card-text">
                  Book available treks and manage your
                  bookings in one place.
                </p>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card h-100 shadow-sm text-center">
              <div class="card-body">
                <h3>✅</h3>
                <h5 class="card-title">Organized Management</h5>
                <p class="card-text">
                  Manage trekking activities with
                  Admin and Staff support.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- About Page -->
    <div
      v-else-if="currentPage === 'about'"
      class="container my-5"
    >
      <h2>About Trekking Management</h2>

      <p class="mt-3">
        The Trekking Management Application helps
        organizers manage treks, staff assignments,
        participants, bookings, and available slots.
      </p>

      <p>
        Trekkers can discover adventures, book treks,
        and view their booking history.
      </p>
    </div>

    
    <!-- Login Page -->
    <Login
    v-else-if="currentPage === 'login'"
    @login-success="handleLoginSuccess"
    />



<!-- Admin Dashboard -->
<AdminDashboard
  v-else-if="
    currentPage === 'admin-dashboard' &&
    loggedInRole === 'admin'
  "
  @manage-treks="changePage('manage-treks')"
  @manage-staff="changePage('manage-staff')"
  @manage-users="changePage('manage-users')"
  @view-bookings="changePage('view-bookings')"
/>


<!-- Manage Treks Page -->
<ManageTreks
  v-else-if="
    currentPage === 'manage-treks' &&
    loggedInRole === 'admin'
  "
  @back="changePage('admin-dashboard')"
/>

<!-- Manage Staff Page -->
<ManageStaff
  v-else-if="
    currentPage === 'manage-staff' &&
    loggedInRole === 'admin'
  "
  @back="changePage('admin-dashboard')"
/>

<!-- Manage Users Page -->
<ManageUsers
  v-else-if="
    currentPage === 'manage-users' &&
    loggedInRole === 'admin'
  "
  @back="changePage('admin-dashboard')"
/>

<!-- Admin View All Bookings -->
<AdminBookings
  v-else-if="
    currentPage === 'view-bookings' &&
    loggedInRole === 'admin'
  "
  @back="changePage('admin-dashboard')"
/>


<!-- Staff Dashboard -->
<StaffDashboard
  v-else-if="
    currentPage === 'staff-dashboard' &&
    loggedInRole === 'staff'
  "
/>

<!-- User Dashboard -->
<UserDashboard
  v-else-if="
    currentPage === 'user-dashboard' &&
    loggedInRole === 'user'
  "
  @my-bookings="changePage('my-bookings')"
  @my-profile="changePage('user-profile')"
/>

<!-- My Bookings Page -->
<MyBookings
  v-else-if="
    currentPage === 'my-bookings' &&
    loggedInRole === 'user'
  "
  @back="changePage('user-dashboard')"
/>

<!-- User Profile Page -->
<UserProfile
  v-else-if="
    currentPage === 'user-profile' &&
    loggedInRole === 'user'
  "
  @back="changePage('user-dashboard')"
/>
    
<!-- Register Page -->
<Register
  v-else-if="currentPage === 'register'"
  @registration-success="changePage('login')"
/>


    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
      <p class="mb-0">
        © 2026 Trekking Management Application
      </p>
    </footer>
  </div>
</template>

<style scoped>
.hero {
  background: linear-gradient(135deg, #198754, #064e3b);
  padding: 110px 20px;
}

.hero h1 {
  font-size: 3rem;
}

.card {
  border: none;
  border-radius: 12px;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
}

footer {
  font-size: 14px;
}

@media (max-width: 576px) {
  .hero {
    padding: 70px 15px;
  }

  .hero h1 {
    font-size: 2rem;
  }
}
</style>
