# Set up the language processing service on a server

service {'nginx.service':
  ensure  => running,
  enable  => true,
  require => [File['sites-enabled'], File['sites-disabled']],
}

file {'sites-available':
  ensure => file,
  path   => '/etc/nginx/sites-available/GoodNews',
  source => '/data/current/etc/nginx/sites-available/GoodNews',
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
}

file {'sites-enabled':
  ensure  => link,
  path    => '/etc/nginx/sites-enabled/GoodNews',
  target  => '../sites-available/GoodNews',
  require => File['sites-available'],
}

file {'sites-disabled':
  ensure => absent,
  path   => '/etc/nginx/sites-enabled/default',
}
