// ******************************************
// REFERENCES DIALOGS: /eference.dialogs.js
// ------------------------------------------
// Version: 1.0
// Date: 20-10-2022

var STATUS = 'change-status';

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $ReferDialog = {
    container    : null,
    box          : null,
    mode         : '',
    state        : new Object(),

    IsTrace      : 0,

    init: function(mode) {
        this.mode = mode
        this.container = $("#"+this.mode+"-confirm-container");
        this.box = $("#"+this.mode+"-request");
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
            keywords['refer confirmation']+' '+keywords[mode+' selected file']+
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

var $ReferenceSubmitDialog = {
    base         : $BaseDialog,

    // ================================
    // Reference Submit Dialog Class
    // ================================

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
                    '::'+($("#item-logsearch-eference").prop('checked') ? 1 : 0).toString()+
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

var $ReferenceHandleDialog = {
    base         : $BaseDialog,

    container    : null,
    box          : null,
    ob           : null,

    // ======================
    // Reference Handle Class
    // ======================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    default_height : 620,

    action       : '',
    command      : null,
    id           : null,
    mode         : null,
    data         : null,
    params       : null,
    oid          : null,
    review_id    : null,
    reference_id    : null,
    report_id    : null,
    is_author    : 0,
    is_executor  : 0,
    save_duedate : null,

    is_show_loader : 0,

    columns      : ['author','title','note','duedate','executor','report','status'],
    buttons      : ['validate','finish','reject','remove'],

    init: function() {
        this.container = $("#"+this.id+"-confirm-container");
        this.oid = $LineSelector.get_id();

        this.is_show_loader = IsShowLoader;
    },

    term: function() {
        if (this.IsTrace)
            alert('term');

        this.clear();

        this.container = null;
        this.box = null;
        this.ob = null;
        this.action = '';
        this.command = null;
        this.id = null;
        this.mode = null;
        this.data = null;
        this.params = null;
        this.oid = null;
        this.review_id = null;
        this.reference_id = null;
        this.report_id = null;
        this.is_author = 0;
        this.is_executor = 0;
        this.save_duedate = null;

        should_be_updated = false;
        selected_menu_action = '';

        is_input_focused = false;

        this.base.onClose();
    },

    clear: function() {
        var self = $ReferenceHandleDialog;

        if (this.IsLog)
            console.log('$ReferenceHandleDialog.clear:', self.columns);

        if (is_null(self.columns))
            return;

        self.columns.forEach(function(name, index) {
            var ob = $("#reference_"+name, self.container);
            if (is_exist(ob)) {
                ob.prop("disabled", false);
                ob.val('');
            }
        });
    },

    state_buttons: function(state) {
        this.buttons.forEach(function(name, index) {
            $("#reference-confirm-button-"+name).button(state);
        });
    },

    set_params: function() {
        this.params = {
            'command':this.command, 
            'review_id': this.review_id,
            'reference_id': this.reference_id,
            'report_id': this.report_id,
            'is_author' : this.is_author ? 1 : 0,
            'is_executor' : this.is_executor ? 1 : 0,
            'reference_title' : $("#reference_title").val(), 
            'reference_note' : $("#reference_note").val(), 
            'reference_status' : $("#reference_status").val(), 
            'reference_duedate' : [$("#reference_duedate").val(), this.save_duedate], 
            'reference_author' : $("#reference_author").val(), 
            'reference_executor' : $("#reference_executor").val(), 
            'reference_report' : $("#reference_report").val(), 
        };

        if (this.IsDebug)
            alert(reprObject(this.params));
    },

    check_size: function() {
        var height = this.default_height;
        var ob = $("#"+this.id+'_author', this.container);

        if (is_exist(ob))
            height += 54;

        this.container.dialog("option", "height", Math.min($_height('available'), height));
    },

    reset: function() {
    },

    lock_scroll: function() {
    },

    unlock_scroll: function() {
    },

    setDefaultSize: function(mode) {
        this.box = $("#"+this.id+"-box");

        var caption = null;
        var s = '';

        switch (mode) {
            case 'reference':
                caption = $("*[class~='order']", $("#"+this.id+"-request")).first();
                s = ' № '+this.oid+'.';
                break;
            default:
                break;
        }

        if (!is_empty(s))
            caption.html(s);

        this.check_size();
    },

    handle: function(response) {
        if (this.IsLog)
            console.log('$ReferenceHandleDialog.handle, mode:'+this.mode, this.id, this.action, response);

        IsShowLoader = this.is_show_loader;

        switch (this.mode) {
            case 'update_reference':
                var self = $ReferenceHandleDialog;

                this.data = response['data'];
                //this.columns = response['columns'];
                this.props = response['props'];

                this.is_author = getattr(this.data, 'is_author', 0);
                this.is_executor = getattr(this.data, 'is_executor', 0);
                this.save_duedate = getattr(this.data, 'duedate', null);
                
                var is_disabled = getattr(this.data, 'is_disabled', 0);

                this.columns.forEach(function(name, index) {
                    var control_id = self.id+'_'+name;
                    var value = self.data[name];
                    var ob = $("#"+control_id, self.container);
                    var prop_disabled = is_disabled ||
                        (self.props['author'].indexOf(name) > -1 && !self.is_author) || 
                        (self.props['executor'].indexOf(name) > -1 && !self.is_executor) ? true : false;

                    if (self.IsLog)
                        console.log(name, value, is_exist(ob));

                    if (is_exist(ob)) {
                        ob.val(value);
                        ob.prop("disabled", prop_disabled);
                    }
                });

                $("#reference_status").val(this.props['status'][0]);

                this.reference_id = this.data['reference_id'];
                this.report_id = this.data['report_id'];

                if (!is_disabled && (this.is_executor || this.is_author)) {
                    if (this.is_executor) {
                        $("#reference-confirm-button-finish").button("disable");
                        $("#reference-confirm-button-reject").button("disable");
                        $("#reference-confirm-button-remove").button("disable");
                        $("#reference-confirm-button-validate").button("enable");
                    }
                    else if (this.is_author) {
                        $("#reference-confirm-button-finish").button("enable");
                        $("#reference-confirm-button-reject").button("enable");
                        $("#reference-confirm-button-remove").button("enable");
                        $("#reference-confirm-button-validate").button("enable");
                    }
                }
                else {
                    $("#reference-confirm-button-finish").button("disable");
                    $("#reference-confirm-button-reject").button("disable");
                    $("#reference-confirm-button-remove").button("disable");
                    $("#reference-confirm-button-validate").button("disable");
                }

                if (this.is_executor)
                    $("#reference_report", this.container).prop("disabled", false);

                this.setDefaultSize('reference');

                this.base.open(this.id);

                break;
            case 'finish_reference':
            case 'reject_reference':
            case 'remove_reference':
            default:
                $PageLoader.refresh_after_review(response);

                this.base.close();

                this.term();
        }
    },

    open: function(ob, mode) {
        if (this.IsLog)
            console.log('$ReferenceHandleDialog.open, mode:'+mode);

        this.ob = ob;

        switch (mode) {
            case 'reference':
                this.id = 'reference';

                $("#reference-confirm-button-finish").button("disable");
                $("#reference-confirm-button-reject").button("disable");
                $("#reference-confirm-button-remove").button("disable");
                $("#reference-confirm-button-validate").button("enable");

                this.clear();

                $("#reference_report", this.container).prop("disabled", true);
        }

        this.init();

        this.setDefaultSize(mode);

        this.base.open(this.id);
    },

    update_reference: function(ob) {
        var subline = ob.parent().parent();
        var review_id = $_get_item_id(subline);

        if (this.IsLog)
            console.log('$ReferenceHandleDialog.update_reference, review_id:'+review_id);

        $SublineSelector.set_current(subline);

        this.ob = ob;

        this.command = 'UPDATE_DECREE';
        this.action = '843';
        this.id = 'reference';
        this.mode = 'update_reference';

        this.review_id = review_id;

        this.params = {
            'command':this.command,
            'review_id':this.review_id,
        };

        this.init();

        IsShowLoader = 0;

        this.state_buttons('disable');

        //$InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ReferenceHandleDialog.handle(x); }, this.params);

        interrupt(true, 5, 500);
    },

    finish: function(mode) {
        if (mode == 0) {
            confirm_action = 'reference:finish';

            $ConfirmDialog.open(
                keywords['Command:Reference finish'] +
                '', 
                600);

            return;
        } else {
            this.command = 'FINISH_DECREE';
            this.action = '857';
            this.mode = 'finish_reference';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ReferenceHandleDialog.handle(x); }, this.params);
    },

    reject: function(mode) {
        if (mode == 0) {
            confirm_action = 'reference:reject';

            $ConfirmDialog.open(
                keywords['Command:Reference reject'] +
                '', 
                500);

            return;
        } else {
            this.command = 'REJECT_DECREE';
            this.action = '857';
            this.mode = 'reject_reference';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ReferenceHandleDialog.handle(x); }, this.params);
    },

    remove: function(mode) {
        if (mode == 0) {
            confirm_action = 'reference:remove';

            $ConfirmDialog.open(
                keywords['Command:Reference remove'] + '<br>' +
                keywords['Item will be removed from database!'] +
                '', 
                550);

            return;
        } else {
            this.command = 'REMOVE_DECREE';
            this.action = '857';
            this.mode = 'remove_reference';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ReferenceHandleDialog.handle(x); }, this.params);
    },

    validate: function() {
        if (this.id == 'reference') {
            this.command = 'SAVE_DECREE';
            this.action = '857';
            this.mode = 'save_reference';

            this.set_params();
        }

        this.state_buttons('disable');

        IsShowLoader = 1;

        should_be_updated = true;
        selected_menu_action = this.action;
        $InProgress(this.ob, 1);
        $Handle(this.action, function(x) { $ReferenceHandleDialog.handle(x); }, this.params);
    },

    cancel: function() {
        if (this.IsTrace)
            alert('cancel');

        this.base.cancel();
        this.term();
    },

    onOpen: function() {
        is_input_focused = true;
    },

    onClose: function() {
        if (this.IsTrace)
            alert('cancel');

        this.term();
    },

    is_focused: function() {
        return this.base.is_focused();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ---------------------------------
    // Refer Create/change/Remove Dialog
    // ---------------------------------

    $("#refer-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:160, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ReferDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ReferDialog.close(); }}
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
            {text: keywords['Run'],    click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $ReferenceSubmitDialog.cancel(); }}
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
            {text: keywords['Run'],    click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Reject'], click: function() { $ReferenceSubmitDialog.cancel(); }}
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

    // ------------------------------
    // Create Handle Reference Dialog
    // ------------------------------

    $("#reference-confirm-container").dialog({
        autoOpen: false,
        width:778,
        height:620,
        position:0,
        buttons: [
            {
                id: "reference-confirm-button-finish",
                text: keywords['Finished'],
                click: function() {
                    $ReferenceHandleDialog.finish(0);
                }
            },
            {
                id: "reference-confirm-button-reject",
                text: keywords['Rejected'],
                click: function() {
                    $ReferenceHandleDialog.reject(0);
                }
            },
            {
                id: "reference-confirm-button-validate",
                text: keywords['Save'],
                click: function() {
                    $ReferenceHandleDialog.validate();
                }
            },
            {
                id: "reference-confirm-button-remove",
                text: keywords['Remove'],
                click: function() {
                    $ReferenceHandleDialog.remove(0);
                }
            },
            {
                id: "reference-confirm-button-cancel",
                text: keywords['Close'],
                click: function() {
                    $ReferenceHandleDialog.cancel();
                }
            }
        ],
        modal: false,
        draggable: true,
        resizable: false,
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        open: function() {
            $ReferenceHandleDialog.onOpen();
        },
        close: function() {
            $ReferenceHandleDialog.onClose();
            $BaseDialog.onClose();
        },
    });
});
