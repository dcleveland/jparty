$(function (){
  $(".clear_err").on("click", function(){
    $(".error_msg_div").hide();
    console.log("clicked!")
  });
  // Set an interval since the dates are loaded via ajax and not always
  // when this is called.
  var int = setInterval(function() {
    if ($("select.date").length > 0) {
      $("select.date").change(function() {
        $("select.round").html('<option class="round">Select a round</option>');
        var game_date = $("option.date:selected").val()
        // Only show valid rounds for a given game_date
        rounds = getGameRounds(game_date);
        $.each(rounds, function(i, round) {
          $("select.round").append('<option class="round" value="'
              + round + '">' + round + '</option>');
        });
      });
      clearInterval(int);
    }
  }, 200);
  $(".error_msg").on("click", function() {
    $(".error_msg_div").hide();
  })
})

ROUND_SELECT_HTML = '<option class=round value="Select a round">'
  +'Select a round</option>'
  + '<option class=round value="1">1</option>' 
  + '<option class=round value="2">2</option>'
  + '<option class=round value="3">3</option>'

// Function to return the size of an array object. Used to count the number of
// rounds in a game, clues in a round/category, etc.
Object.size = function(o) {
  var s = 0, k;
  for (k in o) {
    if (o.hasOwnProperty(k)) {
      s++;
    }
  }
return s;
}

function setLinks() {
  // Function to set click functionality on clue boxes and the question/answer
  // display box.
  $(".clue").on("click", function(){
    qhtml = '<p class="q_display">' + $(this).data("question")
            + '<br><button class="show_ans" data-answer="'
            + $(this).data("answer")
            + '">Show Answer</button><br>'
            + '<p class="answer" ' + 'style="display: none">' 
            + $(this).data("answer").replace(/\\'/g, "'") + '</p></p></div>'
    $(".display").html(qhtml);
    $(".display").css("left", "0px !important");
    // Set position of the clue/answer tags based on the width of the table
    var t = $(".game_table").height();
    $(".q_display").css("top", t);
    var w = ($(".game_table").width() - $(".q_display").width())/2;
    $(".q_display").css("left", w);
    $(".q_display").css("position", "absolute");
    var a_w = ($(".game_table").width() - $(".answer").width())/2;
    $(".answer").css("top", t + 100);
    $(".answer").css("left", a_w);
    // Remove text when a clue is picked.
    $(this).text("");
    $(this).css("background", "blue");
    if ($(this).data("dd") == "1") {
      $(this).text("DD").css("color", "red");
    }
    // bind click function for the show answer button.
    $(".show_ans").on("click", function() {
      $(".answer").css("display", "block");
    });
  });
}


// Error functions
function showDateError() {
  // Date/round selection error messages
  $(".error_msg_div").show();
  $(".error_msg").text('Must provide a date. ');
  $(".error_msg").append('<a class="clear_err">Clear</a>')
}

function showRoundError() {
  // Error message when no round is selected.
  $(".error_msg_div").show();
  $(".error_msg").text('Must specify a round. ');
  $(".error_msg").append('<a class="clear_err">Clear</a>')
}

function showSearchError() {
  // Error message when no query is entered.
  $(".error_msg_div").show();
  $(".error_msg").text('Must provide a query. ');
  $(".error_msg").append('<a class="clear_err">Clear</a>');
}

function clearError() {
  // Function to clear the error message.
  $(".error_msg_div").hide();
  $(".error_msg").text("");
}

function doSearch(query) {
  // Function to get search results (ajax request), parse the JSON and display.
  if (query == "Enter category search term") {
    showSearchError();
    $(".error_msg_div").css("left", ($(window).width()
        - $(".error_msg").width())/2);
    return;
  }
  hideTable();
  $(".game_container").html("")
  $("div.search_results").html("");
  var req = $.ajax({url: "/search/q=" + query});
  req.done(function(data) {
    results = $.parseJSON(data);
    var container = $("div.search_results");
    container.show();
    container.append('<ul class="search_list">');
    $.each(results, function(n, r) {
      var category = r[0].replace(/"/g, "&quot");
      var clean_cat = category.charAt(0) + category.substring(1).toLowerCase();
      var clue_cnt = r[1];
      container.append('<li class="search_cat"><a class="search_cat" data-cat="'
                       + category + '" data-count="' + clue_cnt
                       + '">' + clean_cat + ' (' + clue_cnt
                       + ')</a></li>');
    });
    container.append('</ul>');
    container.css("top", $(".controls").height() + 20);
    container.css("position", "absolute")
    $("a.search_cat").on("click", function() {
      showCategory($(this).data("cat").replace(/&quot/g, '"'));
  });
  });
}

function drawCategoryGrid(grid, index, category) {
  /* Function to draw the game grid for a single category (from search results).
    Implemented a separate function for categories vs. game round since the
    categories have varying numbers of available clues. E.g. "Math" has 98 clues
    but something less common may only have 5.
  */
  $(".game_container").css("width", "100%");
  var c_width = $(".game_container").width();
  clues = $.parseJSON($(".game_container").data("grid_" + index));
  ncols = clues.length
  var html = '<table class="game_table"><tr class="categories">';
  for (i=0; i<6; i++) {
    html += '<td class="cat_cell" data-col="' + i + '">' + category + '</td>';
  }
  html += "</tr>"
  // Draw all cells in a normal sized grid. We'll hide unused ones later.
  var cell_id = 0;
  for(i=1; i<6; i++) {
    html += '<tr class="game_row" data-row="' + i + '">'
    for(j=1; j<7; j++) {
      html += '<td class="clue" data-row="' + i + '" data-col="' + j + '"></td>'
      cell_id += 1;
    }
    html += "</tr>"
  }
  html += '</table><div class="display"></div>'
  $(".game_container").html(html);
  $(".game_container").append('<div class="next_button"><button>Next</button></div>');
  var col_index = 1;
  for (col in clues) {
    var row_index = 1;
    if (clues[col] == {[],[],[],[].[]}) {
      $(".tr").filter("[data-col=" + col_index).hide();
      break;
    }
    for (c in clues[col]) {
      var clue = clues[col][c];
      var cell = $("td.clue").filter('[data-row="' + row_index + '"][data-col="'
                                     + col_index + '"]')
      if (clue) {
      cell.text("$" + clue[4]);
      cell.data("question", clue[2]);
      cell.data("answer", clue[3]);
      cell.data("data-dd=", clue[6]);  
      }
      row_index += 1;
    };
    col_index += 1;
  }
  if ($(".game_container").data("grid_" + (index + 1))) {
    $(".next_button").show();
    $(".next_button").on("click", function() {
      var next_grid = $(".game_container").data("grid_" + index + 1);
      drawCategoryGrid(next_grid, index + 1 , category);
    });
  }
  else {
    $(".next_button").hide();
  }
  // Add vals for unpicked clues.
  var clues = $("td.clue");
  $.each(clues, function(n, e) {
    if (!$(this).data("question")) {
      $(this).data("question", "Unpicked clue");
      $(this).data("answer", "Unknown");
      $(this).data("dd", "0");
      $(this).text("Unpicked");
    }
  })
  $(".game_container").show()
  var gt_width = $(".game_table").width();
  var w_width = $(window).width();
  console.log()
  var l_adjust = (w_width - gt_width)/2
  $(".game_container").css("left", l_adjust);
  $(".game_container").width(c_width - $(".game_table").width());
  var next_left = ($(window).width() - $(".game_table").width())/4 + $(".game_table").width();
  var next_top = ($(".game_table").offset().top + $(".game_table").height()/2 -$(".next_button").height())/2
  $(".next_button").css("left", next_left);
  $(".next_button").css("top", next_top);
  $(".display").html("");
  setLinks();
}

function showCategory(category) {
  $(".search_results").hide();
  var req = $.ajax({url: '/cat_grids/c=' + category, async: false});
  category = category
  req.done(function(data) {
    var cat_data = $.parseJSON(data);
    $.each(cat_data['grids'], function(i, clues) {
      $(".game_container").data("grid_" + i, JSON.stringify(clues));
    });
  });
  var grid0 = $(".game_container").data("grid_0");
  drawCategoryGrid(grid0, 0, category);
  clearError();
  if ($(".game_container").data("grid_1")) {
    $(".next_button").show();
  }
  else {
    $(".next_button").hide();
  }
}


// Game date/round functions

function drawTable(data, round) {
  // Function to draw a grid and add questions/answers to cells' data fields.
  $(".search_results").html("");
  var container = $(".game_container");
  var c_width = container.width();
  var html = '<table class="game_table"><tr class="categories">';
  var roundData = data["rounds"][round];
  var categories = data['categories'][round];
  for (c in categories) {
    html += '<td class="cat_cell">' + categories[c] + '</td>';
  }
  html += '</tr>';
  for (v in data["vals"][round]) {
    html += '<tr>';
    for (c in categories) {
      if (data["vals"][round][v] in data["rounds"][round][categories[c]]) {
        html += '<td class="clue" data-question="' + 
        roundData[categories[c]][parseInt(data["vals"][round][v], 10)]['question']
        + '" ' + 'data-answer="'
        + roundData[categories[c]][parseInt(data["vals"][round][v], 10)]['answer']
        + '" ' + 'data-dd="'
        + roundData[categories[c]][parseInt(data["vals"][round][v], 10)]["dd"]
        + '">$' + data["vals"][round][v] + '</td>'
      }
      else {
        html += '<td class="clue" data-question="Unpicked question."'
          +' data-answer="N/A" data=dd="0">Not Picked</td>'
      };  
      }
      
    html += '</tr>'
  };
  html += '</table><div class="display"></div>'
  container.html(html);
  container.append('<div class="next_button"><button>Next</button></div>');
  container.width(c_width - $(".game_table").width());
  $(".next_button").hide();
  var next_left = ($(window).width() - $(".game_table").width())/4 + $(".game_table").width();
  var next_top = ($(".game_table").offset().top + $(".game_table").height()/2 -$(".next_button").height())/2
  $(".next_button").css("left", next_left);
  $(".next_button").css("top", next_top);
  c_width = $(".game_table").width();
  w_width = $(window).width();
  l_adjust = (w_width - c_width)/2
  $(".game_container").css("left", l_adjust);
  $(".display").html("");
  setLinks();
}


function showGame(game_date, round) {
  $(".game_container").css("width", "100%");
  if(game_date == "Select a date") {
    showDateError();
    $(".error_msg_div").css("left", ($(window).width() - $(".error_msg").width())/2);
    return;
  }
  if(round == "Select a round") {
    showRoundError();
    $(".error_msg_div").css("left", ($(window).width() - $(".error_msg").width())/2);
    return;
  }
  var req = $.ajax({
    url: "/game/id=" + game_date
  }).success(function() {
    var data = $.parseJSON(req.responseText);
    $(".error_msg").text("");
    $(".search_results").hide();
    $(".game_container").show();
    drawTable(data, round);
    $(".next_button").show();
    var next_d_r = getNextGameRound(game_date, round);
    var next_date = next_d_r.date;
    console.log(next_d_r);
    var next_round = next_d_r.round;
    if (!next_round) {
      $(".next_button").hide();
    }
    else {
      $(".next_button").data("date", next_date);
      $(".next_button").data("round", next_round);
      $(".next_button").data("rounds", next_d_r.rounds);
      $(".next_button").on("click", function() {
        $('.date option[value=' + next_date + ']').prop('selected', 'selected')
        resetRounds($(this).data("rounds"));
        $('.round option[value=' + next_round + ']').prop('selected', 'selected')
        console.log("date = " + $(".next_button").data("date") + "; round=" + $(".next_button").data("round"));
        showGame($(this).data("date"), $(this).data("round"));
      });  
    }
  }).error(function() {
    showDateError();
    $(".error_msg_div").css("left", ($(window).width() - $(".error_msg").width())/2);
  });
  $(".search_results").html("")
}

// Get the next valid game date and round.
function getNextGameRound(game_date, round) {
  if ($('option.round').length == parseInt($("option.round:selected").val(), 10) + 1) {
    // need next game
    var next_date = getNextGameDate(game_date);
    var rounds = getGameRounds(next_date);
    var next_round = rounds[0];
    return {date: next_date, round: next_round, rounds: rounds};
  }
  else {
    var rnd = $("option.round:selected").index() + 1;
    var next_round = $('option.round:eq(' + rnd + ')').val();
    var rounds = getGameRounds(game_date);
    return {date: game_date, round: next_round, rounds: rounds};
  }
  
}

function getNextGameDate(game_date) {
  // Get the next valid game date
  $.ajax({url: '/next_date/d=' + game_date, async: false}).done(function(data) {
    date = $.parseJSON(data);
  });
  return date;
}

function getGameRounds(game_date) {
  // Function to get the valid rounds for a given game date.
  var rounds = [];
  req = $.ajax({url: "/game/id=" + game_date, async: false});
  req.done(function(data) {
    round_data = $.parseJSON(req.responseText)['rounds'];
    for (r in round_data) {
      if (Object.size(round_data[r]) > 0) {
        rounds.push(r);
      }
    }
  });
  return rounds;
}


function resetRounds(rounds) {
  $("select.round").html('<option class="round">Select a round</option>');
  $.each(rounds, function(i, round) {
    $("select.round").append('<option class="round" value="' + round + '">' + round + '</option>');
  });
}


function hideTable() {
  $(".game_container").hide();
}

