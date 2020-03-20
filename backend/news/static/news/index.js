$(document).ready(() => {
  console.log(
    localStorage.getItem("visited") === "true"
      ? "Welcome Back!"
      : "Welcome to Good News!"
  );

  const visited = localStorage.getItem("visited");
  if (visited === null) {
    localStorage.setItem("visited", "once");
    window.location = "/about";
  } else if (visited === "once") {
    localStorage.setItem("visited", "true");
    $("#landing").prepend(`
    <p href="/" style="color: yellowgreen; font-size: 24px;">
      It would appear this is your first visit to Good News!
      <a href="/">Click here</a> to be redirected to the Main Page.
    </p>
    `);
  }
});
