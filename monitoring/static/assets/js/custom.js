$('#SSLEnable').on('change', function() {
    if($('#SSLEnable').is(":checked"))
            $("#ssl_content").show();
    else
            $("#ssl_content").hide();
});