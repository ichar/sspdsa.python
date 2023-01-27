// ********************************************
// APPLICATION PAGE DECLARATION: /references.js
// --------------------------------------------
// Version: 1.00
// Date: 20-10-2022

default_submit_mode = 2;
default_action      = '500';
default_log_action  = '501';
default_input_name  = 'refer_id';
default_menu_item   = '';
default_handler     = null; //function(x) { $PageLoader.refresh(x); };
default_params      = {}; //{ 'max-width': $_width('client') };

LINE    = '';
SUBLINE = '';

var is_full_container = 0;

// Flag for 'input' keyboards
var is_input_focused = 0;
var is_no_line_open = 0;

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function log_callback_error(action, errors) {
    if (IsTrace)
        alert('log_callback_error.action:'+action);
}

function log_callback(current_action, data, props) {
    var is_error = getattr(props, 'is_error', 0);
    var show_notification = getattr(props, 'show_notification', 0);
    var message = getattr(props, 'message', null);
    var is_message = !is_empty(message);

    if (IsDebug)
        alert('references.log_callback:'+message+':'+is_error);

    if (is_error)
        $ShowError(message, true, true, false);
    else if (show_notification && is_message)
        $NotificationDialog.open(message); //, 400, 320, keywords['Processing info']);
    else {
        $ReferenceSubmitDialog.close();
    }

    $ReferenceSubmitDialog.is_error = is_error;
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'status', 'batchtype']);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $TabSelector.init();

    tab_init('divisions', 0);
    tab_init('nodes', 0);
    tab_init('messagetypes', 0);
    tab_init('binds', 0);

    init_controller('divisions');

    // ------------------------
    // Start default log action
    // ------------------------

    //interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    function _check(x) { 
        var errors = x['errors']; 

        if (IsDebug)
            alert(errors.length);

        if (errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
        }
        else {
            $NotificationDialog.open(keywords['Message:Request sent successfully']);
        }
    }

    ob = $("#refer_content");

    switch (mode) {
    case 0:
        break;
    case 1:
        if (confirm_action == 'save') {
            $PageLoader.handle_change($("#refer_content"), confirm_action);
        }
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();
}

function $onTabSelect(group) {
    $ReferenceSubmitDialog.activate(group);
}

function $onTablineSelect(ob, alias) {}

function $onTablineUpload(alias) {
    alert('$onTablineUpload.alias:'+alias);
    //$Go('702');
    return 0;
}

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged() {
    //alert($_width('screen-min')-$("#sidebarFrame").width()+':'+$("#line-table").width());
}

function $onCloseDialog(ob) {
    $dropErrorPointer(ob);
}

// ===========================
// Dialog windows declarations
// ===========================

function $onFormSubmit(frm) {
    if (IsTrace)
        alert('references.pagging-from submit');
}

function MakeFilterSubmit(mode, page) {
    //$("#filter-form").attr("action", baseURI);
}

// =========================
// Custom routine assigments
// =========================

function $PageButton(ob) {
    var id = ob.attr("id");
    var x = id.split('_');
    var command = x.length >= 2 ? x[1] : x[0];
    
    //alert(id);

    $InProgress(ob, 1);

    switch (command) {
        case 'save':
            break;
    }
}

var is_error_pointer = false;

function $setErrorPointer(ob) {
    var id = ob.attr('id');
    var maxv = int(ob.prop('max'));
    var minv = int(ob.prop('min'));
    var value = 0;
    try {
        value = int(ob.val());
    }
    catch(e) {}

    var box = $("#check_error");

    var p = $_box_position(ob);

    //alert('input.part.id:'+id+'::'+joinToPrint([minv, maxv, value, p.top, p.left, box.attr('id')]));

    var top = p.top-76;
    var left = p.left-10;

    if (value > maxv) {
        $("#check_error_info").html(keywords['Value should be less then:']+' '+(maxv + 1));
    }
    else if (value < minv) {
        $("#check_error_info").html(keywords['Value should be more then:']+' '+(minv == 0 ? -1: 0));
    }
    else
        return;

    box.css({top: $_get_css_size(top, 'px'), left:$_get_css_size(left, 'px')}).show();

    ob.focus();

    is_error_pointer = true;
}

function $dropErrorPointer(ob) {
    if (is_error_pointer) {
        var box = $("#check_error");

        box.hide();

        is_error_pointer = false;
    }
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // ---------------------
    // Data Section progress
    // ---------------------

    // -----------------
    // Tabline selection
    // -----------------

    $("#data-section").on('click', '.column', function(e) {
        //
        //   Tabline Columns click
        //
        if ($PageLoader.is_shown)
            return;

        var ob = ($(this)).parent();

        if (IsTrace)
            alert('references.click.column:'+ob.attr('id'));

        //init_controller(null);
        $PageScroller.init_state(ob);

        e.stopPropagation();
    });

    $("#data-section").on('click', '.row-button', function(e) {
        //
        //   Tabline Navigate Buttons Cursor Controller click
        //
        var ob = $(this).children('a').eq(0);
        var id = ob.attr('id');
        var link = id.split(':')[1];
        var x = link.split('_');
        var group = x[0];
        var command = x[1];
    
        if (IsTrace)
            alert('references.click.row-button:'+joinToPrint([group, command]));

        $PageScroller.refresh(group, command);

        e.preventDefault();
        e.stopPropagation();
    });

    // -----------------
    // Page Form Buttons
    // -----------------

    $("button.refer-binds-signal", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');

        if (IsTrace)
            alert('click.binds_signal:'+id);

        $PageController.contextmenu_activated(ob);

        e.preventDefault();
        e.stopPropagation();
    });

    $("button[id^='action']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');
        var command = id.split('-')[1];

        if (IsTrace)
            alert('click.command:'+command);

        if (['node_change', 'messagetype_add', 'messagetype_change', 'bind_send'].indexOf(command) > -1 )
            $ReferenceSubmitDialog.open(command);

        e.preventDefault();
        e.stopPropagation();
    });

    $("input[name='node_state']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');

        if (IsTrace)
            alert('state.input.value:'+ob.val());
    });

    $("input.part", this).change(function(e) {
        $setErrorPointer($(this));
    }).on('keydown',function(e) {
        $dropErrorPointer($(this));
    });

    $("input[name='messagetype_priority']", this).click(function(e) {
        var ob = $(this);
        var id = ob.attr('id');
        var value = ob.val();

        $("#messagetype_priority_value").html(value);

        if (IsTrace)
            alert('priority.input.value:'+value);
    });

    // --------------
    // Tabs Data menu
    // --------------

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(1, 1000);
    });

    $(window).scroll(function(e){
        //$PageScroller.checkPosition(0);
    });

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;
        
        if (e.keyCode==27) {                                     // Esc
            $dropErrorPointer(ob);
        }

        if (e.keyCode==13) {                                     // Enter
            // --------------------------------------
            // Application Submit Dialog Class Events
            // --------------------------------------

            if ($ReferenceSubmitDialog.is_focused()) {
                e.stopPropagation();
                $ReferenceSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
            e.stopPropagation();
            switch (selector.group) {
            case 'messagetypes':
                $ReferenceSubmitDialog.open('messagetype_change');
                
                break;
            case 'nodes':
                $ReferenceSubmitDialog.open('node_change');
                break;
            case 'binds':
                $ReferenceSubmitDialog.open('bind_send');
                break;
            }
            return false;
        }

        if (e.keyCode==45) {                                     // Ins
            switch (selector.group) {
            case 'messagetypes':
                $ReferenceSubmitDialog.open('messagetype_add');
                break;
            }
        }

        if ($ReferenceSubmitDialog.is_focused() || is_search_focused)
            return;

        if (IsTrace && IsDeepDebug)
            alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        exit = true;
        
        if (e.shiftKey && e.keyCode==9)                         // Shift-Tab
            init_controller(null);

        else if (e.shiftKey && e.keyCode==79) {                 // Shift-O
            e.stopPropagation();
            $SidebarDialog.activate($(this));
            exit = true;
        }

        // -----------------------
        // Tabline Selector moving
        // -----------------------

        else if (selector.active) {
            if (e.keyCode==38)                                  // Up
                $PageScroller.refresh(null, 'up');
            else if (e.keyCode==40)                             // Down
                $PageScroller.refresh(null, 'down');
            else if (e.keyCode==36)                             // Home
                $PageScroller.refresh(null, 'first');
            else if (e.keyCode==33)                             // PgUp
                $PageScroller.refresh(null, 'pgup');
            else if (e.keyCode==34)                             // PgDown
                $PageScroller.refresh(null, 'pgdown');
            else if (e.keyCode==35)                             // End
                $PageScroller.refresh(null, 'last');
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function search_is_empty() {
    return is_empty($("#searched").val()) ? true : false;
}

function page_is_focused(e) {
    return 0; //$ReferenceSubmitDialog.is_focused();
}

function $_show_page(mode) {
    $ShowPage(mode);
}

function resize(force){
    // orion  viewport::1043:1043:screen::1200:avail::1152:client::862:1043:862:inner-outer::1043:1128: max::1200
    // asus:  viewport::794:794:screen::900:avail::900:client:1052:1052:1052:inner-outer::794:900: max::1052
    // note:  viewport::635:635:screen::768:avail::741:client::1104:1104:1104:inner-outer::635:741: max::1104
    //
    //show_height();
    /*
    var viewport = verge.viewportH();
    var max_height = $_height('max');
    var is_max = win_is_max_height();

    var header = $("#header-section").height();
    var footer = $("#footer-section").height();
    var x = $("#divisions_top").height() + $("#divisions_bottom").height()+(is_max ? 120: 180);
    var available = viewport - (header+footer+x);

    var height = Math.ceil(available/2)-10;

    //alert(joinToPrint(['references.resize.height:', viewport, max_height, is_max, available, header, footer, x, height]));

    $(".view-container").each(function() { 
        $(this).css("height", $_get_css_size(height, 'px'));
        $(this).height(height);
    });
    */
    //if (!(force || is_max)) $onRefreshClick();

    //show_height();
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (references)');

    IsLog = 0;
    IsDebug = 0;
    IsDeepDebug = 0;
    IsTrace = 0;

    current_context = 'references';

    $("#search-context").attr("placeholder", "Найти (имя файла, ТЗ)...");

    //resize(1);

    IsActiveScroller = 0;

    $_init();
});


