// Regular expression from W3C HTML5.2 input specification:
// https://www.w3.org/TR/html/sec-forms.html#email-state-typeemail
var emailRegExp = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

import axios from 'axios'

// Bus
var eventBus = new Vue()

var Composant_of = {
	// data IN
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
	// Fetches posts when the component is created.
  created() {
    axios.get(`http://jsonplaceholder.typicode.com/posts`)
    .then(response => {
      // JSON responses are automatically parsed.
      this.posts = response.data
    })
    .catch(e => {
      this.errors.push(e)
    })

	methods : {
		ajouterarticle : function(){
			var vm = this;
			vm.articles.push(vm.article);
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
			//console.log('changment statut ' + v_id, v_statut	);
			//of.statut = v_statut;
			eventBus.$emit('statut_change',v_id,  v_statut)
			//console.log( " mon of " + of.code_of )
		},
	},
 // OUT : render template

template : "#of_template"

};


var items =  [
	{'id' : 1002, 'isActive': true,  'statut': 'L', 'code_of':'C2018129901', 'date_debut' : '25/12/2018',  'commande': 'F7815003' , 'client' : 'SEPHORA', 'quantite_cde' : 5600}  ,
	{'id' : 1003, 'isActive': false, 'statut': 'S', 'code_of':'C2018129933', 'date_debut' : '23/12/2018',  'commande': 'F7826110' , 'client' : 'MAKE UP', 'quantite_cde' : 10250}  ,
	{'id' : 1004, 'isActive': true,  'statut': 'C', 'code_of':'C2018129956', 'date_debut' : '27/12/2018',  'commande': 'F7813710' , 'client' : 'FRESH', 		'quantite_cde' : 13000}  ,
	{'id' : 1005, 'isActive': true,  'statut': 'P', 'code_of':'C2018129968', 'date_debut' : '21/12/2018',  'commande': 'F7834820' , 'client' : 'BEIERSDORF' , 'quantite_cde': 9500 },
];

var vm = new Vue({
	// root node
	el: "#app", // the instance state

	components : {
		stock : C_stock,
		compof : Composant_of,
	 },

	data:  {
			dict_mois :  ['Janvier' , 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Aout', 'Septembre', 'Novembre', 'Decembre']  ,

			dict_ofs :  items,

			message: {
				text: "Dear Mr. President,\n...",
				maxlength: 255
			},
			submitted: false
		},

		methods: {
			// submit form handler
			change_st: function(elem, v_statut) {
				this.dict_ofs[elem].statut = v_statut;
				var vm = this;
				//vm.dict_ofs[elem].statut = v_statut;
				//vm.dict_ofs.pop();
				console.log("changement de statut " + v_statut);
				//alert("ok");
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
			this.submitted = true;
		},
		// check or uncheck all
		checkAll: function(event) {
			this.selection.features = event.target.checked ? this.features : [];
		}
	  },

	  watch: {
				// watching nested property
				message : function(value) {
				console.log("watch couriel" + value );
				},

				// kilometre
				kilometers : function(val) {
										console.log("watch" + val);
				            this.kilometers = val;
				            this.meters = val * 1000;
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
	props : ['articles'],
	data () {
		return {
			article : '',
		}
	},

	methods : {
		ajouterarticle : function(){
			var vm = this;
			vm.articles.push(vm.article);
		},
	},
	template : '<div>\
		<input type="text" v-model="article" placeholder="ajouter un article"/>\
		<button v-on:click="ajouterarticle">Ajouter !</button>\
		<ul>\
			<li v-for="article in articles"> {{ article }}</li>\
		</ul>\
	</div>'
};
