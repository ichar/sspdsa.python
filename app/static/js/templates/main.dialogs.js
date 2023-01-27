// ****************************************
// BANKPERSO DIALOGS: /bankperso.dialogs.js
// ----------------------------------------
// Version: 1.0
// Date: 22-06-2019

var STATUS = 'change-status';

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $StatusChangeDialog = {
    default_size : {'file'  : [710, screen_size[1]-126], /* 145 */
                    'batch' : [670, 390]
                   },

    container    : null,
    box          : null,
    actual_size  : new Object(),
    state        : new Object(),
    last         : null,

    IsTrace      : 0,

    min_width    : 500,
    min_height   : 200,

    offset_height_init   : {'file':204, 'batch':204},
    offset_height_resize : {'file':190, 'batch':114},
    offset_width_init    : 44,
    offset_width_resize  : 0,

    is_open      : false,

    init: function() {
        this.container = $("#status-confirm-container");
        this.box = $("#status-confirmation-box");
        //this.actual_size = new Object();
        this.state = new Object();
        this.last = null;
    },

    get_id: function() {
        return this.container.attr('id');
    },

    get_mode: function() {
        return this.container.attr('mode');
    },

    set_mode: function(mode) {
        this.container.attr('mode', mode);
    },

    submit: function() {
        $onParentFormSubmit();
    },

    toggle: function(ob) {
        var oid = !is_null(ob) && ob.attr('id');

        if (this.last != null)
            $onToggleSelectedClass(STATUS, this.last, 'remove', null);

        if (this.IsTrace)
            alert('toggle:'+this.last+':'+oid);

        $onToggleSelectedClass(STATUS, ob, 'add', null);

        this.state['mode'] = this.get_mode();
        this.state['value'] = getsplitteditem(oid, ':', 1, '');

        this.last = ob;
    },

    setContent: function(id, data) {
        var mode = this.get_mode();
        var is_change_file = mode == 'file' ? true : false;

        $("#status-request").html(
            keywords['status confirmation']+' '+
            keywords['of '+mode]+
            ' ID:'+id+'? '+
            keywords['Recovery is impossible!']+' '+
            keywords['please confirm']
            );
        $("#status-confirmation").remove();

        var item = '<li class="change-status-item" id="status:ID">'+
                   '<dd class="change-status-id" id="change-status-id:ID">ID</dd>VALUE</li>';

        var content = '';

        data.forEach(function(x, index) {
            content += item
                .replace(/ID/g, x.id)
                .replace(/VALUE/g, x.value);
        });

        var html = 
            '<div class="common-confirmation" id="status-confirmation">'+
            '<h4>'+keywords['status confirmation request']+'</h4>'+
            '<div class="common-box"><div id="status-confirmation-box">'+
              '<ul class="status-'+mode+'">'+content+'</ul>'+
            '</div></div>'+
            (is_change_file ? 
              '<div class="common-box common-panel" id="status-options-box"><p class="attention">'+keywords['Attention']+'</p>'+
                '<label for="status-keep-history"><input type="checkbox" id="status-keep-history" value="1"><span>'+keywords['Option:Keep status history']+'</span></label>'+
              '</div>' : 
              ''
            )+
            '</div>';

        this.container.append(html);
        
        this.box = $("#status-confirmation-box");
    },

    setDefaultSize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size) || force)
            this.actual_size[mode] = this.default_size[mode];

        var size = this.actual_size[mode];

        if (this.IsTrace)
            alert('setDefaultSize:'+mode+':'+this.container.width()+':'+this.container.height()+':'+size+':'+force);

        this.container.dialog("option", "width", size[0]);
        this.container.dialog("option", "height", size[1]);

        // --------------------------------
        // Set default float content height
        // --------------------------------

        if (force)
            this.box
                //.css("width", size[0] - offset_width_init)
                .css("height", (size[1] - this.offset_height_init[mode]).toString()+"px");
    },

    onResize: function(force) {
        var mode = this.get_mode();

        if (!(mode in this.actual_size))
            return false;

        if (this.IsTrace)
            alert('resize:'+mode+':'+this.container.width()+':'+this.container.height()+':'+force);

        if (this.container.width() < this.min_width || this.container.height() < this.min_height) {
            this.setDefaultSize(true);
            return false;
        }

        // -------------------
        // Adjust float height
        // -------------------

        var offset = this.offset_height_resize[mode];
        var new_height = this.container.height() - offset;

        this.box.css("height", new_height.toString()+"px");

        // -------------
        // Save new size
        // -------------

        if (force)
            this.actual_size[mode] = [
                this.container.width(), this.container.height() + offset + 5 // ???
            ];

        return true;
    },

    onOpen: function() {
        this.onResize(false);
        this.box.scrollTop(0);

        this.is_open = true;
    },

    onClose: function() {
        this.container.dialog("close");
        //this.actual_size[this.get_mode()] = [this.container.width(), this.container.height()];
        this.is_open = false;
    },

    confirmation: function(command) {
        this.init();

        var action = 
            command == 'admin:change-filestatus' ? '201' : (
            command == 'admin:change-batchstatus' ? '202' : null
            );

        if (this.IsTrace)
            alert('confirmation:'+action+':'+command);

        $web_logging(action);
    },

    open: function(action, data) {
        var mode = (action == '201' ? 'file' : 'batch');
        var id = SelectedGetItem(mode == 'file' ? LINE : SUBLINE, 'id');

        if (id == null || this.is_open)
            return;

        this.set_mode(mode);
        this.setContent(id, data);

        this.container.dialog("option", "title", keywords['Status confirmation form']);

        this.setDefaultSize(false);

        //this.container.dialog("option", "position", {my:"center center", at:"center center", of:"#dataFrame"});

        this.container.dialog("open");
    },

    confirmed: function() {
        this.close();

        if (this.IsTrace)
            alert('confirmed:'+this.state['mode']);

        if (!('mode' in this.state))
            return;

        var mode = this.state['mode'];
        var id = SelectedGetItem((mode == 'file') ? LINE : SUBLINE, 'id');
        var value = this.state['value'];
        var status_keep_history = $("#status-keep-history").prop("checked") ? 1 : 0;
        var command = 'admin:change-'+mode+'status';

        $("input[name='"+mode+"_id']").each(function() { $(this).val(id); });
        $("#status_"+mode+"_id").val(value);
        $("#status_keep_history").val(status_keep_history);
        $("#command").val(command);

        this.submit();
    },

    close: function() {
        this.onClose();
    }
};

var $OrderDialog = {
    container    : null,
    box          : null,
    state        : new Object(),

    IsTrace      : 0,

    init: function() {
        this.container = $("#order-confirm-container");
        this.box = $("#order-request");
        this.state = new Object();
    },

    get_id: function() {
        return this.container.attr('id');
    },

    get_mode: function() {
        return this.container.attr('mode');
    },

    set_mode: function(mode) {
        this.container.attr('mode', mode);
    },

    submit: function() {
        $onParentFormSubmit();
    },

    toggle: function(ob) {
        this.state['mode'] = this.get_mode();
    },

    is_important: function(mode) {
        return ['create', 'delete'].indexOf(mode) > -1 ? true : false;
    },

    setContent: function(id, data) {
        var mode = this.get_mode();

        this.box.html(
            keywords['order confirmation']+' '+keywords[mode+' selected file']+
            ' ID:'+id+'? '+
            (this.is_important(mode) ? keywords['Recovery is impossible!']+' ' : '')+
            keywords['please confirm']
        );
    },

    open: function(command) {
        this.init();

        var mode = (command == 'admin:create' ? 'create' : (command == 'admin:delete' ? 'delete' : command));
        var id = SelectedGetItem(LINE, 'id');

        if (this.IsTrace)
            alert('open:'+command+':'+id);

        if (id == null)
            return;

        this.set_mode(mode);
        this.setContent(id, null);

        this.toggle(null);

        this.container.dialog("open");
    },

    confirmed: function() {
        this.close();

        if (!('mode' in this.state))
            return;

        var mode = this.state['mode'];
        var id = SelectedGetItem(LINE, 'id');
        var command = 'admin:'+mode;

        $("input[name='file_id']").each(function() { $(this).val(id); });
        $("#command").val(command);

        this.submit();
    },

    close: function() {
        this.container.dialog("close");
    }
};

var $BankpersoSubmitDialog = {
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
                this.command = 'admin:tagsearch';
                this.id = 'tagsearch';
                break;
            case 'logsearch':
                this.command = 'admin:logsearch';
                this.id = 'logsearch';
                break;
            case 'changedate':
                this.command = 'admin:changedate';
                this.id = 'changedate';
                break;
            case 'changeaddress':
                this.command = 'admin:changeaddress';
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
                    '::'+($("#item-logsearch-bankperso").prop('checked') ? 1 : 0).toString()+
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
    // --------------------
    // Status Change Dialog
    // --------------------

    $("#status-confirm-container").dialog({
        autoOpen: false,
        buttons: [
            {text: keywords['Confirm'], click: function() { $StatusChangeDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $StatusChangeDialog.close(); }}
        ],
        modal: true,
        draggable: true,
        resizable: true,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $StatusChangeDialog.onOpen();
        },
        close: function() {
            $StatusChangeDialog.onClose();
        },
        resize: function() {
            $StatusChangeDialog.onResize(true);
        }
    });

    // ----------------------------
    // Order Recreate/Remove Dialog
    // ----------------------------

    $("#order-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:160, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $OrderDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $OrderDialog.close(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
    });

    // -----------------
    // Log Search Dialog
    // -----------------

    $("#logsearch-confirm-container").dialog({
        autoOpen: false,
        width:540,
        height:425,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BankpersoSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BankpersoSubmitDialog.cancel(); }}
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

    // -----------------
    // Tag Search Dialog
    // -----------------

    $("#tagsearch-confirm-container").dialog({
        autoOpen: false,
        width:590,
        height:270,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BankpersoSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BankpersoSubmitDialog.cancel(); }}
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

    // ---------------------------
    // Change Delivery Date Dialog
    // ---------------------------

    $("#changedate-confirm-container").dialog({
        autoOpen: false,
        width:400,
        height:440,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BankpersoSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BankpersoSubmitDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
        /*
        open: function() {
            $("#changedate-context").css("height", "200px");
        }
        */
    });

    // ------------------------------
    // Change Delivery Address Dialog
    // ------------------------------

    $("#changeaddress-confirm-container").dialog({
        autoOpen: false,
        width:600,
        height:330,
        position:0,
        buttons: [
            {text: keywords['Run'],    click: function() { $BankpersoSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $BankpersoSubmitDialog.cancel(); }}
        ],
        modal: true,
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
