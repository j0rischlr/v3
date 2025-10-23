<template>
  <div class="movie-container">
    <div
      class="movie-background"
      :style="{ backgroundImage: movie ? `url(${movie.backdrop_path})` : 'none' }"
    ></div>

    <div v-if="loading" class="loading-container">
      <div class="loading-bar-container">
        <div class="loading-bar"></div>
      </div>
    </div>

    <div v-else-if="movie" class="movie-layout">
      <!-- Note du film en haut à droite -->
      <div class="movie-rating-top">
        <span class="rating-value">{{ animatedRating }}</span>
        <span class="rating-max">/10</span>
      </div>

      <!-- Informations du film en bas (1/3 inférieur) -->
      <div class="movie-info-bottom">
        <h1 class="movie-title">{{ movie.title }}</h1>

        <div class="movie-metadata">
          <span v-if="movie.genres && movie.genres.length > 0" class="movie-genres">
            {{ movie.genres.join(', ') }}
          </span>
          <span v-if="movie.runtime">
            {{ formatRuntime(movie.runtime) }}
          </span>
          <span v-if="movie.release_date">
            {{ formatDate(movie.release_date) }}
          </span>
        </div>

        <p class="movie-overview">{{ movie.overview }}</p>

        <div class="bottom-section">
          <div class="movie-actions">
            <a
              v-if="movie.trailer_url"
              :href="movie.trailer_url"
              target="_blank"
              rel="noopener noreferrer"
              class="trailer-button"
            >
              Bande annonce
            </a>
            <NuxtLink to="/" class="random-button">
              Suivant
            </NuxtLink>
          </div>

          <div v-if="movie.actors && movie.actors.length > 0" class="actors-section">
            <div class="actors-list">
              <NuxtLink
                v-for="actor in movie.actors"
                :key="actor.id"
                :to="`/actor/${actor.id}`"
                class="actor-item"
              >
                <div class="actor-avatar">
                  <img
                    v-if="actor.profile_path"
                    :src="actor.profile_path"
                    :alt="actor.name"
                    class="actor-image"
                  />
                  <div v-else class="actor-placeholder">
                    {{ actor.name.charAt(0) }}
                  </div>
                </div>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="error-container">
      <h2 class="title has-text-white">Erreur</h2>
      <p class="has-text-white">{{ error }}</p>
      <NuxtLink to="/" class="random-button">
        Retour
      </NuxtLink>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const config = useRuntimeConfig()
const movie = ref(null)
const loading = ref(false)
const error = ref(null)
const animatedRating = ref('0.0')

const fetchMovieDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const movieId = route.params.id
    const response = await $fetch(`${config.public.apiBaseUrl}/api/movie/${movieId}`)
    movie.value = response
  } catch (err) {
    error.value = 'Impossible de charger les informations du film.'
    console.error('Erreur:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Date inconnue'
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatRuntime = (minutes) => {
  if (!minutes) return ''
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  if (hours === 0) {
    return `${mins}min`
  }

  return `${hours}h${mins.toString().padStart(2, '0')}`
}

const animateRating = (targetValue) => {
  const duration = 1500 // durée de l'animation en ms
  const startTime = performance.now()
  const startValue = 0

  const animate = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)

    // Fonction d'easing (ease-out cubic)
    const easeProgress = 1 - Math.pow(1 - progress, 3)

    const currentValue = startValue + (targetValue - startValue) * easeProgress
    animatedRating.value = currentValue.toFixed(1)

    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }

  requestAnimationFrame(animate)
}

// Watcher pour animer la note quand le film change
watch(() => movie.value?.vote_average, (newRating) => {
  if (newRating !== undefined) {
    animateRating(newRating)
  }
})

onMounted(() => {
  fetchMovieDetails()
})
</script>
