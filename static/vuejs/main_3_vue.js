
Vue.filter('arrondi', function (value, number) {
  return parseFloat(value.toFixed(number))
})


// instance view de propostion DA simulation
var vm2 = new Vue({
    el: '#app3',
    delimiters: ['[[', ']]'],
    data : {
      message : "*",
      erreur : "",
      edit_msg : "Modifiez",
      articles:  Object,
      isActive : true,
      transition_select: 'fade',
      columns: ['code_of', 'produit'],
      filterKey: String,
      sortOrders : {},
      sortKey: 'produit',


    },  //

    computed: {

      sortedProduct: function() {
        if(this.articles.length > 0){
          //console.log("tab size = " + this.articles[0].fields.code_of)
          //this.articles.sort(this.compare)
          return this.articles
        }
      }
    },

    mounted() {
      //do something after mounting vue instance
      //var cac_id = "237"
      var url = `/da/api/cac/${cac_id}/`
      fetch(url).then(
    	 function (response) {
    		   return  response.json()
    		   console.log("api data  !!")
    		 }
       ) .then( json => { this.articles = json},
    	   console.log("api retour  !!" + this )
       )
       .catch((err)=>console.log(err))

    },

    methods: {
     compare(a, b){
        console.log("api retour  !!" + a.fields.code_of )

        if (a.fields.code_of < b.fileds.code_of)
          return -1;
        if (a.fileds.code_of > b.fileds.code_of)
          return 1;
        return 0;
      },

      // toper article selectionner
      grouper_produit(cac_id){
        // grouper par produit
        // redirect
        var url =  `/da/cac_grouped/${ cac_id }/`
        location.replace(url)
        console.log("grouper par produit !! ***"  + url )

        return true
      },

      sortBy(key) {
        console.log("sortBy en fonction ...")
        this.sortKey = key
        this.sortOrders[key] = this.sortOrders[key] * -1
        //this.articles.forEach(function (key) { this.sortOrders[key] = 1 })
        //this.articles.sort(function (key) { this.sortOrders[key] = 1 })
        //sortKey: '',
        //sortOrders: sortOrders
        this.articles.sort(this.compare)
      }
    }
  });
