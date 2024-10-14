var eventBus = new Vue()

Vue.component(
  'product-tabs',
  {
    props : {
      nb_ofs : ""
    } ,
    delimiters: ['[[', ']]'],
    data : function() {
        return {
        total : 100,
        selectedTab : 'Panier',
        count_cart : Object,
        messages : [],
      }
    },

    mounted:function(){
      var url = `/da/cart/count_cart/`

      eventBus.$on('add_to_card', () => {
          //this.messages.push('add_to_card emitted !!')
          this.refresh_cart()
        })

      fetch(url).then(
       function (response) {
          var keys_objects = $.map(response, function(element,index) {return index})
          console.log("cart_count !!=" + response )
          return  response.json()
      })
      .then( json => { this.count_cart = json},
          console.log("this.count_cart = " + this.count_cart )
      )
      .catch((err)=>console.error(err))
      },

      methods: {
        refresh_cart() {
          var url = `/da/cart/count_cart/`
          fetch(url).then(
           function (response) {
              var keys_objects = $.map(response, function(element,index) {return index})
              console.log("refresh_cart .."  )
              return  response.json()
          })
          .then( json => { this.count_cart = json},
              console.log("this.count_cart = " + this.count_cart )
          )
          .catch((err)=>console.error(err))
          },
        },

    template : `
      <div>
        <div class="content" >
            <li>  <span  v-show="this.count_cart.cart_count  > 0" @add_to_card="refresh_cart" class="label-primary badge badge-secondary">Panier:[[ this.count_cart.cart_count ]] </span> </li>
            <li>  <span  v-show="nb_ofs  > 0" class="label-primary badge badge-secondary">ofs : [[ nb_ofs ]] </span> </li>

        </div>
      </div> `

  }
)

// composant produit
Vue.component(  'product-item',
{
  props : {
    article: Object,
  },

  methods: {
     emitAddToCart(id) {
          console.info("event add_to_card a été emit" + id)
          eventBus.$emit("add_to_card",  id)
      },

      emitDelToCart() {
          this.cart = this.cart > 0 ?  this.cart - 1 : 0
      },
      emitUpdateProduct(img) {
          //console.info("image avant " + this.image)
          this.image = img
          //console.info("image " + img)
      }
  },

  data : function(){
    return {
        reviews : [],
        selectedArt  : 'Panier',
        image : this.image,
        cart : this.cart,
        id : this.id,
          }
  },

  template : "#prod_template"
})

//import axios from 'axios';

var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data : {
      semaine : init_semaine,
      annee : init_annee,
      machines:null,
      message : "*",
      erreur : "",
      edit_msg : "Modifiez",
      edit_week : false,
      edit_year : false,
      machine_selected: false,
      current_machine:"",
      ofs : ofs_list,
      errors: [],
      toggle:true,
      selected : "",

    },  // fin data

    watch : {
      current_machine : function(val) {
        console.log("valeur de la machine change !!!" + val)
        this.machine_selected=true
      },
      semaine : function(val){
        if ( this.semaine > 52 ||  this.semaine == 0 || this.semaine == null) {
          console.log(" semaine invalide !!!" + typeof(this.semaine))
          //this.semaine = 21
          this.erreur = " numero de semaine invalide !!!"
        } else this.erreur = ""
      },

    },

    methods: {
        // use Moment to calculate the local week number
        weekday(inputDate){
          var currentLangCode = 'fr'; // en francais
          var aujourdhui  = new Date()
          var now = moment();
          //return moment(inputDate).local().week();
          return moment(inputDate).lang(currentLangCode).week()
        },

        // Validation form
        validate_form(event){
              this.errors = [];
              if(this.current_machine && this.semaine){
                console.log(" pas de machine saisie !!!" )
                var form  = event.target
                form.submit()
                return true
              }
              event.preventDefault();
              this.errors = [];

              if (!this.semaine) {
                this.errors.push('Saisir un numero de semaine !.');
              }
              if (!this.annee) {
                this.errors.push('Annee manquante !.'  );
              }
              if (!this.current_machine) {
                this.errors.push('Machine manquante !.' + this.selected)
              }

              return false
        },
        // ajout d'un of dans le panier
        add_of_cart(event, code_of, quantite){
          // ajout d'un of dans le panier
          console.log("Quantite modifier: " + quantite );
          quantite = parseInt(quantite)
          const  url = `/da/cart/additem/${code_of}/${quantite}/`
            // post la demande
            $.get( url ).done(function(data, status, error)  {
              console.log("ca marche item ajouter: " )
              this.toggle = !this.toggle;
              $(event.target).toggleClass("btn-warning");
              $(event.target).toggleClass("btn btn-default");
              // emission signal add_to_cart
              eventBus.$emit("add_to_card")

              $("#id_content_msg").html(status);
            }).fail(function(data, status, error) {
              console.log("error serveur : " +  data);
            });
        },
        // add
        add_ofs_cart(e){
          // ajout d'un ensemble d'of dans le panier
          //list_checkbox_checked  =  $(".form-check-input").is(':checked')
          list_checkbox_checked  =  $(".form-check-input")
          //list_checkbox_checked.filter(item => item.checked).map(name => name.name)
          //

          if(list_checkbox_checked.length > 0){
            $.each(list_checkbox_checked , function( key, value ) {
                if(value.checked){
                  var quantite_prevue = $("#quantite_prevue_" + value.name).val()

                  vm.add_of_cart(e, value.name,  quantite_prevue)
                  console.log("add groupe of " + key + "val=" + quantite_prevue )
                }
              });
          }
        },

        // charger la liste des of
        charge_list_of() {
            this.cart = this.cart > 0 ?  this.cart - 1 : 0
            url = "/da/home/" + this.semaine + "/" + this.annee ;
            console.log("reload sur la semaine !!" + this.semaine)
            location.href = url;
            location.replace(url)
            // on ferme la saisie
            this.edit_week = false
            this.edit_msg = "Modifier"
            this.machine_selected =true
        },

        updateWeek() {

          if(this.edit_week == false)
          {
            this.edit_week = true
            this.edit_msg = "Fermez"
          }else{
            this.edit_week = false
            this.edit_msg = "Modifier"
          }
        },

        updateYear() {
          if(this.edit_year == false)
          {
            this.edit_year = true
            this.edit_msg = "Fermez"
          }else{
            this.edit_year = false
            this.edit_msg = "Modifier"
          }
        }
    },

    mounted : function(){
      // ajouter une option choisissez au debut list_box
      $( "#id_machines").push("<option disabled value=''>Choisissez</option>")

      // fetch charger par defut la semaine en cours
      var aujourdhui  = new Date()
      var d = aujourdhui.getDate()
      var mois = aujourdhui.getMonth()
      var annee = String(aujourdhui.getFullYear())
      var an = annee[2] + annee[3]

      var weekday = moment(aujourdhui).local().week()

      // fetch
      //var url = `/da/home/da/${weekday}/${an}/`
      //console.error("url charger par defaut  !!" +  url)
      console.log("reload sur la semaine !!" + this.semaine)
      //location.href = url;
      //location.replace(url)
      // on envoie

    } // fin mounted

});// fin de view
