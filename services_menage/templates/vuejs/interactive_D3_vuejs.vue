<template>
<div class="match" :style="matchStyle" @mouseover="onMouseover">
  <table>
    <tr @mouseover="$store.commit('setTeam', home)" :class="home === $store.state.team ? 'chosen' : null" @mouseout="$store.commit('clearTeam')">
      <td style="border-bottom:solid 1px black;">{{this.home}}</td>
      <td class="score" style="border-bottom:solid 1px black;">{{this.homeScore}}</td>
    </tr>
    <tr @mouseover="$store.commit('setTeam', away)" :class="away === $store.state.team ? 'chosen' : null" @mouseout="$store.commit('clearTeam')">
      <td>{{this.away}}</td>
      <td class="score">{{this.awayScore}}</td>
    </tr>
  </table>
</div>
</template>

<script>
// Park Sungryeol - sungryeolp@gmail.com
const rawData = {
  matchId: 5,
  home: 'Incheon',
  away: 'Seoul',
  homeScore: 1,
  awayScore: 2,
  children: [
    {
      matchId: 4,
      home: 'Incheon',
      away: 'Gangwon',
      homeScore: 2,
      awayScore: 1,
      children: [
        {
          matchId: 1,
          home: 'Mokpo',
          away: 'Incheon',
          homeScore: 2,
          awayScore: 3,
        },
        {
          matchId: 2,
          home: 'Bucheon',
          away: 'Gangwon',
          homeScore: 3,
          awayScore: 4,
        }
      ]
    },
    {
      matchId: 3,
      home: 'Busan',
      away: 'Seoul',
      homeScore: 0,
      awayScore: 5,
    },
  ]
}

const store = new Vuex.Store({
  state: {
    matchId: null,
    team: null,
  },
  mutations: {
    setMatchId (state, matchId) {
      state.matchId = matchId;
    },
    setTeam (state, team) {
      state.team = team;
    },
    clearTeam (state) {
      state.team = null;
    },
  }
})

// d3 is automatically imported in Codepen projects
// import * as d3 from 'd3';

Vue.component('match', {
  name: 'Match',
  
  computed: {
    matchStyle() {
      return {
        left: `${this.xpos}px`,
        top: `${this.ypos}px`,
      };
    },
  },
  props: [
    'xpos',
    'ypos',
    'home',
    'away',
    'homeScore',
    'awayScore',
    'matchId',
  ],
  methods: {
    onMouseover() {
      this.$store.commit('setMatchId', this.matchId);
    }
  }
})

const bracketApp = new Vue({
  store,
  data: () => ({
    rawData,
    width: 1000,
    height: 500,
    padding: 50,
    matches: [],
    root: {}, // root is exposed for global
    matchWidth: 100,
    matchHeight: 50,
    tree: null, // tree is also exposed for global
  }),
  mounted() {
    this.refresh();
  },
  methods: {
    refresh() {
      this.tree = d3.tree()
        .size([this.height - this.matchHeight, this.width - (this.matchWidth * 2 + this.padding * 2)]);
      this.root = this.tree(d3.hierarchy(this.rawData));
      this.matches = this.root.descendants();
      this.drawLinks();
    },
    drawLinks() {
      const g = d3.select('svg > g');
      const links = g.selectAll('path.link')
        .data(this.root.descendants().slice(1));
      const elbow = d3.line()
        .curve(d3.curveStep);
      links.enter()
        .append('path', 'g')
        .attr('class', 'link')
        .attr('d', function (d) {
          let targetY = d.x;
          let sourceY = d.parent.x;
          let targetX = d.y;
          let sourceX = d.parent.y;
          if (d.data.homeScore < d.data.awayScore) {
            targetY = d.x + 25;
          } else {
            targetY = d.x - 25;
          }
          return elbow([[sourceX, sourceY], [targetX, targetY]])
        })
      
    }
  }
}).$mount('#bracketApp');
</script>


<style scoped>
body {
  background: #00416A;  /* fallback for old browsers */
background: -webkit-linear-gradient(to right, #E4E5E6, #00416A);  /* Chrome 10-25, Safari 5.1-6 */
background: linear-gradient(to right, #E4E5E6, #00416A); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
  color: #FFFDF7;
  text-shadow: 0 0 3px black;
}
#bracketApp {
  display:flex;
  justify-content:center;
}
.details {
  background-color:rgba(0,0,0,.3);
  padding:10px;
}
.bracket-div {
  position: relative;
}
.bracket-svg {
  position: absolute;
  .background {
    fill: black;
    fill-opacity:0.3;
  }
  .link {
    fill: none;
    stroke: lightgray;
    stroke-width: 1px;
  }
}
.match {
  background-color:#2CA58D;
  display:block;
  color: #FFFDF7;
  border-radius: 10px;
  position:absolute;
  width: 150px;
  height: 100px;
  table {
    width: 100%;
    height: 100%;
    padding:5px;
    border:none;
    .score{
      text-align:center;
    }
    .chosen {
      background-color: rgba(0,0,0,0.3);
      transition:.3s;
    }
  }
}
</style>