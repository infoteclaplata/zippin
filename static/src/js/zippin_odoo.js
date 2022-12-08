odoo.define('zippin_pickup_points.payment', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function() {
        'use strict';

        $('select[name="zippin_car_suc"]').bind("change", function(ev) {

            document.getElementById("zippin_oca_suc").selectedIndex = "0";
            document.getElementById("zippin_and_suc").selectedIndex = "0";

            let res = $('select.zippin_car_suc').val();
            var inicio = res.indexOf("carrier_id:");
            var fin = res.indexOf(",point_id:");
            let carrier_id = res.substring(inicio+11, fin);

            var inicio = res.indexOf("point_id:");
            var fin = res.indexOf(",name:");
            let point_id = res.substring(inicio+9, fin);

            var inicio = res.indexOf("name:");
            var fin = res.indexOf(",address:");
            let name = res.substring(inicio+5, fin);

            var inicio = res.indexOf("address:");
            var fin = res.indexOf("}");
            let address = res.substring(inicio+8, fin);

            ajax.jsonRpc('/shop/zippin_odoo', 'call', {
                'carrier_id': carrier_id,
                'point_id': point_id,
                'name': name,
                'address': address
            })
        });


        $('select[name="zippin_oca_suc"]').bind("change", function(ev) {

            document.getElementById("zippin_car_suc").selectedIndex = "0";
            document.getElementById("zippin_and_suc").selectedIndex = "0";

            let res = $('select.zippin_oca_suc').val();
            var inicio = res.indexOf("carrier_id:");
            var fin = res.indexOf(",point_id:");
            let carrier_id = res.substring(inicio+11, fin);

            var inicio = res.indexOf("point_id:");
            var fin = res.indexOf(",name:");
            let point_id = res.substring(inicio+9, fin);

            var inicio = res.indexOf("name:");
            var fin = res.indexOf(",address:");
            let name = res.substring(inicio+5, fin);

            var inicio = res.indexOf("address:");
            var fin = res.indexOf("}");
            let address = res.substring(inicio+8, fin);

            ajax.jsonRpc('/shop/zippin_odoo', 'call', {
                'carrier_id': carrier_id,
                'point_id': point_id,
                'name': name,
                'address': address
            })
        });


        $('select[name="zippin_and_suc"]').bind("change", function(ev) {

            document.getElementById("zippin_car_suc").selectedIndex = "0";
            document.getElementById("zippin_oca_suc").selectedIndex = "0";

            let res = $('select.zippin_and_suc').val();
            var inicio = res.indexOf("carrier_id:");
            var fin = res.indexOf(",point_id:");
            let carrier_id = res.substring(inicio+11, fin);

            var inicio = res.indexOf("point_id:");
            var fin = res.indexOf(",name:");
            let point_id = res.substring(inicio+9, fin);

            var inicio = res.indexOf("name:");
            var fin = res.indexOf(",address:");
            let name = res.substring(inicio+5, fin);

            var inicio = res.indexOf("address:");
            var fin = res.indexOf("}");
            let address = res.substring(inicio+8, fin);

            ajax.jsonRpc('/shop/zippin_odoo', 'call', {
                'carrier_id': carrier_id,
                'point_id': point_id,
                'name': name,
                'address': address
            })
        });

        $('li.list-group-item').bind("click", function(ev) {

            document.getElementById("zippin_car_suc").selectedIndex = "0";
            document.getElementById("zippin_oca_suc").selectedIndex = "0";
            document.getElementById("zippin_and_suc").selectedIndex = "0";

            ajax.jsonRpc('/shop/zippin_odoo', 'call', {
                'carrier_id': '-1',
                'point_id': '-1',
                'name': '-1',
                'address': '-1'
            })
        });
    });
});