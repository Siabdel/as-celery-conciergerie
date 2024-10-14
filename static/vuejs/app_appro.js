		// Regular expression from W3C HTML5.2 input specification:
// https://www.w3.org/TR/html/sec-forms.html#email-state-typeemail
//import moment from 'moment'

var emailRegExp = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

// Bus
var eventBus = new Vue()


// register modal component
Vue.component('modal', {
  template: '#modal-cac-template',

  //--- methods
  methods: {

      // API valider_ligne_da
      deleteDa(da_id){
          // envoie de la validation
          var url = `/da/cac/delete_da/${da_id}/`
          console.log("deleteDa ... !!" + url)

          fetch(url).then(
           function (response) {
              console.log("Confirmation delete  !!" + response)
              // redirect
              //location.href = "/da/cac/list/"
              location.replace("/da/cac/list/")
              return  response
          }).catch((err)=>console.error(err))
       },
    },

})


Vue.config.productionTip = false
Vue.filter('formatDate', function(value) {
  if (value) {
    return moment(String(value)).format('DD/MM/YYYY HH:mm')
  }
});



var Composant_of = {
  // OUT : render template
  template : "#cac_template",
	// data IN
	delimiters: ['[[', ']]'],
	props :  {
		elem : Object,
		index : Number,
	},

	data () {

		return {
			checked : false,
			active : false,
      showModal : false,
			form_active : true,
			key : this.index,
			comment : "",
			csrfmiddlewaretoken : "",
			url_show : "/da/cac/details/" + this.elem.pk,
			url_update_da : "/da/cac_ext_update/updateda/" + this.elem.pk,
			url_print : "/da/cac_ext_print/print/" + this.elem.pk,
			url_export : "/da/cac/export/" + this.elem.pk,
			url_delete_da : "/da/cac/delete_da/" + this.elem.pk,
      ConfirmeDeleteDa : this.emitConfirmeDeleteDa,
			}
	},

  loaded: function(){
    //
    eventBus.$on('emit_confirme_del_da', (demande_appro_id) => {
      console.log("je recoie  le signale 'emit_confirme_del_da' ..." + this.da_courante)
    })
  },

  mounted : function() {
    eventBus.$on('emit_confirme_del_da', (demande_appro_id) => {
      console.log("je recoie  le signale 'emit_confirme_del_da' ..." + this.da_courante)
    })
  },


	methods : {
    todo_it : function(){
      //
      console.log("todo it ..." + this.da_courante)

    }
    ,
    emitConfirmeDeleteDa(){
        // emission d'un signal signal_delete_da
        //this.$emit('signal_delete_da', da_id)
        console.log(" suppression   da= " )
    },

    emit_open_modal_confirm(cac_id){
      eventBus.$emit('open_modal', cac_id)
      console.log("j'envoie signale 'open_modal'")

    },

		changeStatut(index, of){
			console.log( " mon of index " + elem.csrfmiddlewaretoken )
			this.ofs[index].statut = 'P'
			elem.code_of = 'P'
			//this.ofs.[index].statut = 'P'
		},

		EmitchangeStatut: function(  v_id, v_statut) {
			//console.log('changment statut ' + v_id, v_statut	)
			//elem.statut = v_statut
			eventBus.$emit('statut_change',v_id,  v_statut)
			//console.log( " mon of " + elem.code_of )
		},


		checkComment_ajax : function(cac_id){
			var django_url = `/da/cac/addcomment/${cac_id}/`
			// const data = new URLSearchParams(new FormData(formComment))
			var csrf_token = '{{csrf_token}}'
			//var data = $("#formComment").serialize()
			var data = $("#formComment").serialize()
			//var data = JSON.stringify(simpledata)
			// add csrfmiddlewaretoken
			var cle_csrf = $( "input[name='csrfmiddlewaretoken']" ).val()

			data = {
				'comment' : this.comment,
				'csrfmiddlewaretoken' : this.csrfmiddlewaretoken
				}

			$.ajax({
				url: django_url,
				type: 'POST',
				beforeSend: function (xhr) {
						xhr.setRequestHeader( 'X-CSRFToken', cle_csrf )
				},
				data: data,
				contentType: 'json',
				success : function(code_html, statut){
					console.log("success post ajax" + statut)
				},
				complete : function(resultat, statut){
					console.log("complete post ajax" + resultat)
				},
				error : function(resultat, statut, erreur){
					console.log("error post ajax" + erreur)
					}
		 });
			return true;
		},


	 checkComment : function(cac_id ){
			var url = `/da/addcomment/${cac_id}/`
			// const data = new URLSearchParams(new FormData(formComment))
			var csrf_token = '{{csrf_token}}'
			//var data = $("#formComment").serialize()
			var form = $("#formComment").serialize()
			//var data_f = JSON.stringify(form)

			// add csrfmiddlewaretoken
			var cle_csrf = $( "input[name='csrfmiddlewaretoken']" ).val()
			//var form = new FormData($(formulaire).name);

			data = {
					'cac_id' :  cac_id ,
				'comment' :  this.comment ,
				'csrfmiddlewaretoken' : cle_csrf ,
			}
			///QueryDict: {u'comment': [u'ZZZZZZZZZZZZZ'], u'csrfmiddlewaretoken': [u'DMbU0yI7I9lVACrt7agLPHu9bzkMoektWe7sd1N85rVvfbRk60rNEJZ10ntNESoF']}
			js_data = JSON.stringify(data) // on serialise data

			//Debug var keys_objects = $.map(response, function(element,index) {return index})
			//alert(keys_objects)

		 fetch(url,
			{
		    method : 'POST',
				headers : {
					   //'X-Requested-With': 'XMLHttpRequest',
						//'Content-Type': 'application/json',
						"Content-Type": "application/x-www-form-urlencoded",
						//"Content-Type": "multipart/form-data",
        		'Accept': 'application/json',
						'X-CSRFToken': cle_csrf,
					},
				//body : JSON.stringify({'comment' : 'wwwwwwwwwwwww' }),
				body :  js_data,
				//credentials: 'same-origin'
			})
			.then(response => console.log(response))
			.then( function (response) {
				console.log("add commentaire cac_id=%s ..." % data)
				// redirect
				//location.replace("/da/cac/list/")
				return  response
		 }).catch((err)=>console.error(err))

		 this.form_active = false
		 return true;
	 },



	},


}

var vm = new Vue({
	// root node
	el: "#app", // the instance state
  delimiters: ['[[', ']]'],
	components : {
		compof : Composant_of,
	},

	data:  {
			dict_ofs : [],
			currentSort : 'name',
			currentSortDir : 'asc',
			pageSize : 8,
	 		currentPage : 1,
			active : false,
      showModal : false,
			message: {
				text : "...",
				maxlength : 255
			},
			submitted: false,
      da_courante : null,
		},

		mounted() {
			//do something after mounting vue instance
			//var url = `/da/api/cac/${cac_id}/`
			var url = `/da/cac/apilistcac/`
			fetch(url).then(
			 function (response) {
         	 console.log("api data  !!" + response)

					 return  response.json()
				 }
			 ) .then( json => { this.dict_ofs = json},
         //Debug
         console.log("api retour   keys_objects !!" +  this.dict_ofs)
			 )
			 .catch((err)=>console.log(err))
       //listene

       eventBus.$on('open_modal',  (cac_id) => {
         this.showModal = true ;
         this.da_courante = cac_id
         console.log("je recoie bien le signale 'open modal' et ouvre j'ouvre la box "  + cac_id)
        })

        // je recoie un signal suppression DA
        eventBus.$on('emitSuppressionDa', (demande_appro_id) => {
          console.log("je recoie  le signale 'emitSuppressionDa' ..." + damnande_appro_id)
          this.suppression_da(demande_appro_id)
        });

        eventBus.$on('emit_confirme_del_da', (demande_appro_id) => {
          console.log("je recoie  le signale 'emit_confirme_del_da' ..." + this.da_courante)
        })

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
				//vm.dict_ofs.pop().log("changement de statut " + v_statut)
				//alert("ok")
				//this.dict_ofs = []
			},

		// check or uncheck all
		submit: function() {
			this.submitted = true
		},
		// check or uncheck all
		checkAll: function(event) {
			this.selection.features = event.target.checked ? this.features : []
      //console.log("checkall : this.selection.features " + this.selection.features)
		}


	  },

	  watch: {
				// watching nested property
				message : function(value) {
				console.log("watch couriel" + value )
				},

		}, //fin watch

		onload : function(v_id, v_statut){
			eventBus.$on('statut_change',  () => { this.dict_ofs[v_id].statut = v_statut });
		}, // bizzarement ça ne marche pas , marche mieux dans onmount()
})
