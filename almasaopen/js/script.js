/* Author: 

*/

$("input[name=start]").change(function() {
	$("#startfile").text($(this).val());
})

$("input[name=finish]").change(function() {
	$("#finishfile").text($(this).val());
})



$(document).ready(function () {
    $("form").change(function() {
        if ($('input[name="start"]').val() != "" && $('input[name="finish"]').val() != "" ) {
            $('input[type="submit"]').removeAttr("disabled").focus().val("Registrera!");
        }
    });
});









