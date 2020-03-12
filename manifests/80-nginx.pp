# Configure nginx to host the current release of GoodNews

package {'nginx':
  ensure => installed,
}

service {'nginx.service':
  ensure    => running,
  enable    => true,
  subscribe => [File['sites-enabled'], File['sites-disabled']],
}

file {'sites-disabled':
  ensure  => absent,
  path    => '/etc/nginx/sites-enabled/default',
  require => Package['nginx'],
}

file {'sites-available':
  ensure  => file,
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  path    => '/etc/nginx/sites-available/GoodNews',
  source  => '/data/current/etc/nginx/sites-available/GoodNews',
  require => Package['nginx'],
}

file {'sites-enabled':
  ensure  => link,
  path    => '/etc/nginx/sites-enabled/GoodNews',
  target  => '../sites-available/GoodNews',
  require => File['sites-available'],
}
