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

    $("#extra").click(function() {
        $("textarea[name=extra]").show().focus();
        $(this).hide();
        return false;
    });

    $("canvas").hide();
    $("#photothumbs > *").click(function() {
        $(this).rotate();
    });
    
    $('#ulform input[type="submit"]').click(function() {
        $(this).val("Laddar upp filer").attr("disabled", "disabled");
        $("#ulform").submit();
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
            if (window.File && window.FileReader && window.FileList) {
                createThumb(evt);
            } else {
                $("#photothumbs").show().text("I Chrome, Firefox och Opera kan man rotera foton!").css("height", "auto");
            }
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
            var image = $("<img>")
                        .attr("src", e.target.result)
                        .hide()
                        .attr("id", "foo"+evt.target.name)
                        .get(0);
            $("#photothumbs").append(image);
            if (!!document.createElement('canvas').getContext) {
                $("canvas." + evt.target.name).show();
                image.onload = function() {
                    var canvas = $("#photothumbs ." + evt.target.name).
                                attr('rot', 0).
                                attr('height', 125).
                                attr('width', (image.width/image.height)*125);
                    var canvasContext = canvas.get(0).getContext('2d');

                    canvasContext.drawImage(image, 0, 0, (image.width/image.height)*125, 125);

                };
            };
            
        };
    })(file);
    if (!$("#photothumbs").is(":visible")) {
        $("#photothumbs").slideDown(1000, function() {
            reader.readAsDataURL(file);
        });
    } else {
        reader.readAsDataURL(file);
    }
}

function deleteComment (commentid, raceid) {
    jQuery.post('/removecomment',
            {
                commentid: commentid,
                raceid: raceid
            });

}

jQuery.fn.choose = function(f) {
  $(this).bind('choose', f);
};


jQuery.fn.file = function() {
  return this.each(function() {
    var btn = $(this);
    var pos = btn.offset();
                
    function update() {
      pos = btn.offset();
      file.css({
        'top': pos.top,
        'left': pos.left,
        'width': btn.width(),
        'height': btn.height()
      });
    }

    btn.mouseover(update);

    var hidden = $('<div></div>').css({
      'display': 'none'
    }).appendTo('body');

    var file = $('<div><form></form></div>').appendTo('body').css({
      'position': 'absolute',
      'overflow': 'hidden',
      '-moz-opacity': '0',
      'filter':  'alpha(opacity: 0)',
      'opacity': '0',
      'z-index': '2'    
    });

    var form = file.find('form');
    var input = form.find('input');
    
    function reset() {
      var input = $('<input type="file" multiple>').appendTo(form);
      input.change(function(e) {
        input.unbind();
        input.detach();
        btn.trigger('choose', [input]);
        reset();
      });
    };
    
    reset();

    function placer(e) {
      form.css('margin-left', e.pageX - pos.left - offset.width);
      form.css('margin-top', e.pageY - pos.top - offset.height + 3);          
    }

    function redirect(name) {
      file[name](function(e) {
        btn.trigger(name);
      });
    }

    file.mousemove(placer);
    btn.mousemove(placer);

    redirect('mouseover');
    redirect('mouseout');
    redirect('mousedown');
    redirect('mouseup');

    var offset = {
      width: file.width() - 25,
      height: file.height() / 2
    };

    update();
  });
};


