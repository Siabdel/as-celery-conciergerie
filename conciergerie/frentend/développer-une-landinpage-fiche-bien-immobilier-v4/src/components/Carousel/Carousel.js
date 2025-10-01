
export default {
  name: 'Carousel',
  props: {
    images: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      currentIndex: 0,
    };
  },
  methods: {
    goToPrevious() {
      const isFirstSlide = this.currentIndex === 0;
      this.currentIndex = isFirstSlide ? this.images.length - 1 : this.currentIndex - 1;
    },
    goToNext() {
      const isLastSlide = this.currentIndex === this.images.length - 1;
      this.currentIndex = isLastSlide ? 0 : this.currentIndex + 1;
    },
    goToSlide(slideIndex) {
      this.currentIndex = slideIndex;
    },
  },
  template: `
    <div class="carousel-container shadow-lg">
      <div
        class="carousel-slide"
        :style="{ transform: 'translateX(-' + currentIndex * 100 + '%)' }"
      >
        <img v-for="(image, index) in images" :key="index" :src="image" :alt="'Slide ' + (index + 1)" />
      </div>
      <button class="carousel-control prev" @click="goToPrevious">
        <i class="bi bi-chevron-left"></i>
      </button>
      <button class="carousel-control next" @click="goToNext">
        <i class="bi bi-chevron-right"></i>
      </button>
      <div class="carousel-indicators">
        <div
          v-for="(image, index) in images"
          :key="index"
          class="indicator"
          :class="{ active: currentIndex === index }"
          @click="goToSlide(index)"
        ></div>
      </div>
    </div>
  `
};
