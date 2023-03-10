// **********************************
// CENTER DIALOGS: /center.dialogs.js
// ----------------------------------
// Version: 1.0
// Date: 14-01-2023

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $CenterSubmitDialog = {
    base         : $BaseDialog,

    // =============================
    // Center Submit Dialog Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : null,
    command      : null,
    group        : null,
    mode         : null,
    id           : null,
    current      : null,
    keys         : [],

    is_error     : false,

    init: function() {
        this.container = $("#"+this.id+"-confirm-container");
    },

    callback: function() {
        return this.base.callback();
    },

    is_focused: function() {
        return this.base.is_focused();
    },

    get_row_item: function(key) {
        return $(".log-"+key, this.current);
    },

    get_form_item: function(key) {
        return $("#"+this.mode+"_"+key, this.box);
    },

    set_data: function(key, default_value) {
    },

    get_data: function(key, default_value) {
    },

    clean_data: function(key, value) {
    },

    disable: function(key) {
    },

    enable: function(key) {
    },

    set: function(x) {
    },

    activate: function(group) {
        this.current = tablines[group].get_current();
        if (is_null(this.current))
            return;
        
        this.group = group;

        if (this.IsDebug)
            alert('$CenterSubmitDialog.activate:'+group+':'+this.current.attr('id'));

        switch (group) {
            case 'capacities':
                break;
            case 'speeds':
                break;
        }
    },

    open: function(action) {
        this.id = this.mode;

        this.init();

        this.setDefaultSize();
    },

    setDefaultSize: function(command) {
        var self = $CenterSubmitDialog;
        this.box = $("#"+this.mode+"-box");

        if (is_empty(command))
            command = this.command;

        var is_open = true;

        switch (this.mode) {
            case 'capacities':
                break;
            case 'speeds':
                break;
        }

        if (is_open) 
            this.base.open(this.id);
    },

    submit: function(params) {
    },

    confirmed: function() {
    },

    cancel: function() {
        this.close();
    },

    close: function() {
        $onCloseDialog(null);
        this.base.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ---------------------------------
    // Refer Create/Change/Remove Dialog
    // ---------------------------------

    $("#capacities-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:452, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $CenterSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $CenterSubmitDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });

    $("#speeds-confirm-container").dialog({
        autoOpen: false,
        width:540,
        height:260,
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $CenterSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $CenterSubmitDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });
});
