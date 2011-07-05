/* Author: 

*/




$(document).ready(function () {
    $('input[type="file"]').change(function(evt) {
        if ($('input[name="start"]').val() != "" && $('input[name="finish"]').val() != "" ) {
            $('input[type="submit"]').removeAttr("disabled").focus().val("Registrera!");
        }
        if (!getFileType(evt).match('image.*')) {
            alert(evt.target.files[0].name + " är inte ett foto!");
            $('input[type="submit"]').attr("disabled", "disabled").val("Välj start och målfil");
            evt.target.value = "";
        }
        return false;
    });
});


function getFileType(evt) {
    var files = evt.target.files; // FileList object
    return files[0].type;
}









