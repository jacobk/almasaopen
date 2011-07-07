/* Author: 

*/

jQuery.fn.rotate = function() {
    var image = $("#photothumbs img#foo"+this.attr("class")).get(0);
    var canvas = this;
    var canvasContext = canvas.get(0).getContext('2d');
    var width = this.width();
    var height = this.height();
    canvas.attr('width', height);
    canvas.attr('height', width);
    var currRot = canvas.attr("rot");
    var newRot = (parseInt(currRot)+90)%360;
    $("#"+this.attr("class")+"rot").val(newRot);
    canvas.attr('rot', newRot);
    canvasContext.rotate(newRot * Math.PI / 180);
    switch(newRot) {
        default :
        case 0 :
            canvasContext.drawImage(image, 0, 0, height, width);
            break;
        case 90 :
            canvasContext.drawImage(image, 0, -height, width, height);
            break;
        case 180 :
            canvasContext.drawImage(image, -height, -width, height, width);
            break;
        case 270 :
            canvasContext.drawImage(image, -width, 0, width, height);
            break;
    };
}

$(document).ready(function () {

    $("#photothumbs > *").click(function() {
        $(this).rotate();
    });
    
    $('input[type="file"]').change(function(evt) {
        if ($('input[name="start"]').val() != "" && $('input[name="finish"]').val() != "" ) {
            $('input[type="submit"]').removeAttr("disabled").focus().val("Registrera!");
        }
        if (!getFileType(evt).match('image.*')) {
            alert(evt.target.files[0].name + " är inte ett foto!");
            $('input[type="submit"]').attr("disabled", "disabled").val("Välj start och målfil");
            evt.target.value = "";
        } else {
            createThumb(evt);
        }
        return false;
    });
});


function getFileType(evt) {
    var files = evt.target.files; // FileList object
    return files[0].type;
}

function createThumb(evt) {
    var file = evt.target.files[0];

    var reader = new FileReader();
    reader.onload = (function(photo) {
        return function(e) {
            if ($("#photothumbs img#foo"+evt.target.name).length) {
                $("#photothumbs img#foo"+evt.target.name).remove();
            }
            $("canvas." + evt.target.name).show();
            var image = $("<img>")
                        .attr("src", e.target.result)
                        .hide()
                        .attr("id", "foo"+evt.target.name)
                        .get(0);
            $("#photothumbs").append(image);
            image.onload = function() {
                var canvas = $("#photothumbs ." + evt.target.name).
                            attr('rot', 0).
                            attr('height', 125).
                            attr('width', (image.width/image.height)*125);
                var canvasContext = canvas.get(0).getContext('2d');

                canvasContext.drawImage(image, 0, 0, (image.width/image.height)*125, 125);

            };
            
        };
    })(file);
    if ($("#photothumbs > canvas").is(":empty")) {
        $("#photothumbs").slideDown(1000, function() {
            reader.readAsDataURL(file);
        });
    } else {
        reader.readAsDataURL(file);
    }
}

//$("#ulform").submit(function() {
    //$.post('/upload',
        //{
            //start: $("canvas.start").get(0).getContext('2d').getImageData(0, 0, 200, 200).data,
            //finish: $("canvas.finish").get(0).getContext('2d').getImageData(0, 0, 200, 200).data
        //},
        //function(data) {});
    //return false;
//});





