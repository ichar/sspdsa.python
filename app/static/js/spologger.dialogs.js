// ***************************************************
// APPLICATION PAGE DECLARATION: /spologger.dialogs.js
// HELPER FUNCTION CONTROLS MANAGER
// ---------------------------------------------------
// Version: 1.0
// Date: 22-06-2019

var STATUS = 'change-status';

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $SpologgerSubmitDialog = {
    base         : $BaseDialog,

    // =============================
    // Bankpesro Submit Dialog Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    command      : null,
    id           : null,
    mode         : null,

    callback: function() {
        return this.base.callback();
    },

    is_focused: function() {
        return this.base.is_focused();
    },

    setDefaultSize: function() {
        this.base.open(this.id);

        switch (this.mode) {
            case 'changedate':
                // chain a few methods for the first datepicker, jQuery style!
                $datepicker.pikaday('show').pikaday('currentMonth');
                break;
        }
    },

    submit: function() {
        $onParentFormSubmit();
    },

    open: function(mode) {
        if (this.base.opened)
            return;

        this.mode = mode;

        switch (this.mode) {
            case 'tagsearch':
                this.command = 'spoin:tagsearch';
                this.id = 'tagsearch';
                break;
            case 'logsearch':
                this.command = 'spoin:logsearch';
                this.id = 'logsearch';
                break;
            case 'changedate':
                this.command = 'spoin:changedate';
                this.id = 'changedate';
                break;
            case 'changeaddress':
                this.command = 'spoin:changeaddress';
                this.id = 'changeaddress';
                break;
        }

        this.setDefaultSize();
    },

    verified: function() {
        this.confirmed();
    },

    confirmed: function() {
        this.base.close();

        switch (this.mode) {
            case 'tagsearch':
                var value = $("#tagsearch-context").val();
                $("#specified").val(value);
                $("#command").val(this.command);
                break;
            case 'logsearch':
                var value = 
                $("#logsearch-context").val()+
                    '::'+($("#logsearch-apply-filter").prop('checked')? 1 : 0).toString()+
                    '::'+($("#item-logsearch-exchange").prop('checked') ? 1 : 0).toString()+
                    '::'+($("#item-logsearch-spologger").prop('checked') ? 1 : 0).toString()+
                    '::'+($("#item-logsearch-sdc").prop('checked') ? 1 : 0).toString()+
                    '::'+($("#item-logsearch-infoexchange").prop('checked') ? 1 : 0).toString();
                $("#specified").val(value);
                $("#command").val(this.command);
                break;
            case 'changedate':
                var value = $("#changedate").val();
                $("#specified").val(value);
                $("#command").val(this.command);
                break;
            case 'changeaddress':
                var value = 
                $("#changeaddress-context").val()+
                    '::'+($("#changeaddress-recno").val())+
                    '::'+($("#changeaddress-branch").val());
                $("#specified").val(value);
                $("#command").val(this.command);
                break;
        }

        this.submit();
    },

    cancel: function() {
        this.base.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // ----------------------------
    // Logger Recreate/Remove Dialog
    // ----------------------------

    $("#logger-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:160, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $LoggerDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $LoggerDialog.close(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
    });
});
