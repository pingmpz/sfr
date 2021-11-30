//-- VALIDATE CONTROL
remove_valid_many = (input_ids) => { for(var i = 0;i < input_ids.length;i++) remove_valid(input_ids[i]); }
valid_many = (input_ids) => { for(var i = 0;i < input_ids.length;i++) valid(input_ids[i]); }
invalid_many = (input_ids) => { for(var i = 0;i < input_ids.length;i++) invalid(input_ids[i]); }

function remove_valid(input_id){
  $("#"+input_id).removeClass("is-invalid");
  $("#"+input_id).removeClass("is-valid");
}

function valid(input_id){
  $("#"+input_id).addClass("is-valid");
  $("#"+input_id).removeClass("is-invalid");
}

function invalid(input_id){
  $("#"+input_id).addClass("is-invalid");
  $("#"+input_id).removeClass("is-valid");
}

//-- INPUT CONTROL
setZeroInputs = (input_ids) => { for(var i = 0;i < input_ids.length;i++) if($("#"+input_ids[i]).val() == "") $("#"+input_ids[i]).val("0"); }

emptyInputs = (input_ids) => { for(var i = 0;i < input_ids.length;i++) $("#"+input_ids[i]).val(""); }

//-- USEFUL FUNCTION
capitalizeFirstLetter = (str) => str.charAt(0).toUpperCase() + str.slice(1);

function frontZero(str, length){
  var result = str;
  for(var i = str.length;i < length;i++) result = "0" + result;
  return result;
}

function generateRandomCode(length) {
  var result = '';
  var characters = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz123456789'; // remove i l o 0
  // var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for ( var i = 0; i < length; i++ ) result += characters.charAt(Math.floor(Math.random() * characters.length));
  return result;
}

function roundToTwo(num) {
  return +(Math.round(num + "e+2")  + "e-2");
}

//-- DATE & TIME
function getFullDateTime(datetime) {
   var result = "";
   var year = datetime.getFullYear();
   var month = frontZero((datetime.getMonth() + 1).toString(), 2);
   var date = frontZero(datetime.getDate().toString(), 2);
   var hour = frontZero(datetime.getHours().toString(), 2);
   var minute = frontZero(datetime.getMinutes().toString(), 2);
   var second = frontZero(datetime.getSeconds().toString(), 2);
   result = date+"-"+month+"-"+year+", "+hour+":"+minute+":"+second;
   return result;
}

getFullDateTimeFromString = (str) => getFullDateTime(new Date(str));

function getDiffMin(start_date_time, stop_date_time){
  var diff = Math.abs(stop_date_time - start_date_time);
  var minutes = Math.floor((diff/1000)/60);
  return minutes;
}
