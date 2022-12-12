odoo.define('zippin_shipping.payment', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function() {
        'use strict';

        $('select[name="zippin_car_suc"]').bind("change", function(ev) {

            document.getElementById("zippin_oca_suc").selectedIndex = "0";
            document.getElementById("zippin_and_suc").selectedIndex = "0";

            let res = $('select.zippin_car_suc').val();
            var i = res.indexOf("carrier_id:");
            var f = res.indexOf(",point_id:");
            let carrier_id = res.substring(i+11, f);

            var i = res.indexOf("point_id:");
            var f = res.indexOf(",name:");
            let point_id = res.substring(i+9, f);

            var i = res.indexOf("name:");
            var f = res.indexOf(",address:");
            let name = res.substring(i+5, f);

            var i = res.indexOf("address:");
            var f = res.indexOf("}");
            let address = res.substring(i+8, f);

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
            var i = res.indexOf("carrier_id:");
            var f = res.indexOf(",point_id:");
            let carrier_id = res.substring(i+11, f);

            var i = res.indexOf("point_id:");
            var f = res.indexOf(",name:");
            let point_id = res.substring(i+9, f);

            var i = res.indexOf("name:");
            var f = res.indexOf(",address:");
            let name = res.substring(i+5, f);

            var i = res.indexOf("address:");
            var f = res.indexOf("}");
            let address = res.substring(i+8, f);

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
            var i = res.indexOf("carrier_id:");
            var f = res.indexOf(",point_id:");
            let carrier_id = res.substring(i+11, f);

            var i = res.indexOf("point_id:");
            var f = res.indexOf(",name:");
            let point_id = res.substring(i+9, f);

            var i = res.indexOf("name:");
            var f = res.indexOf(",address:");
            let name = res.substring(i+5, f);

            var i = res.indexOf("address:");
            var f = res.indexOf("}");
            let address = res.substring(i+8, f);

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