		// Regular expression from W3C HTML5.2 input specification:
// https://www.w3.org/TR/html/sec-forms.html#email-state-typeemail
var emailRegExp = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/


// Bus
var eventBus = new Vue()

var Composant_of = {
	// data IN
	delimiters: ['[[', ']]'],
	props :  {
		of : Object,
		index : Number,
	},

	data () {

		return {
			//ofs : Array,
			checked : true,
			active : true,
			statut : this.statut,

			}
	},


	methods : {
		ajouterarticle : function(){
			var vm = this
			vm.articles.push(vm.article)
		},

		supprimer(elem){
			this.$emit('supp', elem)
		},

		changeStatut : function(index, of){
			console.log( " mon of index " + of.code_of )
			this.ofs[index].statut = 'P'
			of.code_of = 'P'

			//this.ofs.[index].statut = 'P'
		},

		EmitchangeStatut: function(  v_id, v_statut) {
			//console.log('changment statut ' + v_id, v_statut	)
			//of.statut = v_statut
			eventBus.$emit('statut_change',v_id,  v_statut)
			//console.log( " mon of " + of.code_of )
		},
	},
 // OUT : render template

template : "#of_template"

}

var vm = new Vue({
	// root node
	el: "#app", // the instance state
  delimiters: ['[[', ']]'],
	components : {
		stock : C_stock,
		compof : Composant_of,
	 },

	data:  {
			dict_ofs : [],
			currentSort:'name',
			currentSortDir:'asc',
			pageSize:8,
	 		currentPage:1,
			active : true,
			message: {
				text: "...",
				maxlength: 255
			},
			submitted: false
		},

		mounted() {
			//do something after mounting vue instance
			//var url = `/da/api/cac/${cac_id}/`
			var url = `/ofsce/api/apilist/`
			fetch(url).then(
			 function (response) {
					 return  response.json()
					 console.log("api data  !!")
				 }
			 ) .then( json => { this.dict_ofs = json},
				 console.log("api retour  !!" + this )
			 )
			 .catch((err)=>console.log(err))

		},

		computed:{
			sortedCats:function() {
	      return this.dict_ofs.sort((a,b) => {
	        let modifier = 1
	        if(this.currentSortDir === 'desc') modifier = -1
	        if(a[this.currentSort] < b[this.currentSort]) return -1 * modifier
	        if(a[this.currentSort] > b[this.currentSort]) return 1 * modifier
	        return 0
	      }).filter((row, index) => {
	        var start = (this.currentPage-1)*this.pageSize
	        var end = this.currentPage*this.pageSize
	        if(index >= start && index < end) return true
					return false
      })
    }
		},

		methods: {
			// tri
			sort:function(elem) {
				console.log("sort by me !!" + elem )
				//if s == current sort, reverse
				if(elem === this.currentSort) {
				 this.currentSortDir = this.currentSortDir==='asc'?'desc':'asc'
				}
				this.currentSort = elem
			},
 			// paginator
			nextPage:function() {
				if((this.currentPage*this.pageSize) < this.dict_ofs.length) this.currentPage++
			},
			prevPage:function() {
				if(this.currentPage > 1) this.currentPage--
			},

			// submit form handler
			change_st: function(elem, v_statut) {
				this.dict_ofs[elem].statut = v_statut
				var vm = this
				//vm.dict_ofs[elem].statut = v_statut
				//vm.dict_ofs.pop()
				console.log("changement de statut " + v_statut)
				//alert("ok")
				//this.dict_ofs = []
			},
		// supprimer un item
		 remove : function(item) {
			var i = this.dict_ofs.indexOf(item)
			alert("ok" + i)
			if (i > -1) {
			  this.dict_ofs.splice(i, 1)
			}
		  },
		// check or uncheck all
		submit: function() {
			this.submitted = true
		},
		// check or uncheck all
		checkAll: function(event) {
			this.selection.features = event.target.checked ? this.features : []
		}
	  },

	  watch: {
				// watching nested property
				message : function(value) {
				console.log("watch couriel" + value )
				},

				// kilometre
				kilometers : function(val) {
										console.log("watch" + val)
				            this.kilometers = val
				            this.meters = val * 1000
				         	},

				meters : function (val) {
				        this.kilometers = val/ 1000
				        this.meters = val
									},
		}, //fin watch

		onload : function(v_id, v_statut){
			eventBus.$on('statut_change',  () => { this.dict_ofs[v_id].statut = v_statut })
		},
})



var C_stock = {
	delimiters: ['[[', ']]'],
	props : ['articles'],
	data () {
		return {
			article : '',
		}
	},

	methods : {
		ajouterarticle : function(){
			var vm = this
			vm.articles.push(vm.article)
		},
	},
	template : '<div>\
		<input type="text" v-model="article" placeholder="ajouter un article"/>\
		<button v-on:click="ajouterarticle">Ajouter !</button>\
		<ul>\
			<li v-for="article in articles"> {{ article }}</li>\
		</ul>\
	</div>'
}
