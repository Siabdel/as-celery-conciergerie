
import { fabric } from 'fabric';

export default {
  name: 'FloorPlan',
  props: {
    floorPlan: Object,
  },
  data() {
    return {
      selectedApt: null,
      fabricCanvas: null,
      resizeObserver: null,
      thisPropertyId: 'apt-4b',
    };
  },
  created() {
    if (this.floorPlan.apartments[this.thisPropertyId]) {
      this.selectedApt = this.floorPlan.apartments[this.thisPropertyId];
    }
  },
  mounted() {
    if (!this.$refs.canvas) return;

    const canvasWrapper = this.$refs.canvas.parentElement;
    if (!canvasWrapper) return;

    const canvas = new fabric.Canvas(this.$refs.canvas, {
      selection: false,
      width: canvasWrapper.clientWidth,
      height: canvasWrapper.clientHeight,
    });
    this.fabricCanvas = canvas;

    this.drawPlan();

    this.resizeObserver = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      canvas.setWidth(width).setHeight(height);
      this.drawPlan();
    });

    this.resizeObserver.observe(canvasWrapper);
  },
  beforeUnmount() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.fabricCanvas) {
      this.fabricCanvas.dispose();
    }
  },
  methods: {
    drawPlan() {
      const canvas = this.fabricCanvas;
      canvas.clear();
      const objects = [];

      this.floorPlan.buildingPlan.forEach(apt => {
        const isThisProperty = apt.id === this.thisPropertyId;

        const polygon = new fabric.Polygon(apt.points, {
          fill: isThisProperty ? 'var(--secondary-color)' : '#e9ecef',
          stroke: 'white',
          strokeWidth: 4,
          selectable: false,
          hoverCursor: 'pointer',
          aptId: apt.id,
        });

        const text = new fabric.Text(apt.label, {
          left: polygon.left + (polygon.width / 2),
          top: polygon.top + (polygon.height / 2),
          fontSize: 16,
          fill: isThisProperty ? 'white' : 'var(--dark-color)',
          originX: 'center',
          originY: 'center',
          selectable: false,
          hoverCursor: 'pointer',
        });

        const group = new fabric.Group([polygon, text], {
          selectable: false,
          aptId: apt.id,
        });
        
        group.on('mouseover', () => {
          if (apt.id !== this.thisPropertyId) {
            (group.item(0)).set('fill', '#d3d8db');
            canvas.renderAll();
          }
        });

        group.on('mouseout', () => {
          if (apt.id !== this.thisPropertyId) {
            (group.item(0)).set('fill', '#e9ecef');
             canvas.renderAll();
          }
        });

        group.on('mousedown', () => {
          const aptDetails = this.floorPlan.apartments[apt.id];
          if (aptDetails) {
            this.selectedApt = aptDetails;
          }
        });

        objects.push(group);
      });
      canvas.add(...objects);
      canvas.renderAll();
    },
  },
  template: `
    <section>
      <h2 class="section-title">Plan de l'étage</h2>
      <div class="floorplan-container">
        <div class="row g-4">
          <div class="col-lg-7">
            <div class="floorplan-canvas-wrapper">
              <canvas ref="canvas"></canvas>
            </div>
             <small class="form-text text-muted mt-2">Survolez et cliquez sur un lot pour voir les détails. Le lot en orange est celui présenté.</small>
          </div>
          <div class="col-lg-5">
            <div class="floorplan-details h-100">
              <div v-if="selectedApt">
                <h4>Détails du lot: {{ selectedApt.name }}</h4>
                <p class="lead">Surface totale: <strong>{{ selectedApt.area }} m²</strong></p>
                <div class="room-list">
                  <h6>Détail des pièces :</h6>
                  <ul class="list-unstyled">
                    <li v-for="room in selectedApt.rooms" :key="room.name" class="room-item">
                       <span><i class="bi bi-square me-2" style="color: var(--primary-color)"></i>{{ room.name }}</span>
                       <strong>{{ room.area }} m²</strong>
                    </li>
                  </ul>
                </div>
              </div>
              <div v-else class="prompt">
                <p class="h5"><i class="bi bi-cursor me-2"></i>Sélectionnez un appartement sur le plan pour afficher ses informations.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  `
};
