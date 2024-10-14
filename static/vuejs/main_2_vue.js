var eventBus = new Vue()

// register modal component
Vue.component('modal', {
  template: '#modal-template',
  methods: {
     emitValidationDa(id) {
          console.info("validation emit  **" + id)
          //eventBus.$emit("validation", id)
          this.valider_ligne_da(id)
      },

      // API valider_ligne_da
      valider_ligne_da(da_id){
          // envoie de la validation
          var url = `/da/cart/validateda/${da_id}/`
          fetch(url).then(
           function (response) {
              console.log("valider_ligne_da excuter !!" + response)
              // redirect
              //location.href = "/da/cac/list/"
              location.replace("/da/cac/list/")
              return  response
          }).catch((err)=>console.error(err))

       },
    },

})

Vue.filter('arrondi', function (value, number) {
  return parseFloat(value.toFixed(number))
})


// instance view de propostion DA simulation
var vm2 = new Vue({
    el: '#app2',
    delimiters: ['[[', ']]'],
    data : {
      message : "*",
      erreur : "",
      edit_msg : "Modifiez",
      edit_week : false,
      edit_year : false,
      machine_selected: false,
      articles:  Object,
      isActive : true,
      old_of  : '',
      show : false,
      transition_select: 'fade',
      showModal: false,
      selectAll:false
    },  //

    mounted() {
      //do something after mounting vue instance
      var url = "/cart/api/da/simulee/"
      fetch(url).then(
    	 function (response) {
          //console.log("api data  !!")
          return  response.json()
    		 }
       )
       .then( json => { this.articles = json},
    	   console.log("api retour  !! ..." + this.articles )
       )
       .catch( (err)=> console.error(err) )

    },

    methods: {

      checkAll(event){
      		var target = $(event.target);
      		if($(target).is(":checked")){
      				//$('.btn-warning').toggleClass("btn-warning")
              target.prop('checked', false)
              $('.btn-warning').trigger('click').addClass("btn-success");
              console.log("list est checked : " + target)
      			}else {
                target.prop('checked', true);
                console.log("list est unchecked : ");
                $('.btn-success').trigger('click')
                $('.btn-warning').removeClass("btn-success");
                $('.btn-warning').addClass("btn-warning");

            }
      	},
      // toper article selectionner
      select_article_ligneda(event, product_id) {
        var url = `/da/ajax/lda/selected/selecteditem/${product_id}`

        fetch(url).then(
      	 function (response) {
           console.log("product selectionner  !!" + event.target.name);
           //$(event.target).addClass("btn btn-success");
           //$(event.target).removeClass("btn-warning");
           $(event.target).toggleClass("btn-warning");
           //location.reload()
      		   return  response
      		 }).catch((err)=>console.error(err)) }
      },

      // alerter si of est changer
      alertOFChange(){
        console.log("Of a changer !!")
      }

  });
